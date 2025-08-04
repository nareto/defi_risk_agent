from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import asyncio
import logging
import json
from typing import AsyncGenerator, Dict, Any
from contextlib import asynccontextmanager
import os

from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.runnables import RunnableConfig

from src.agent import AgentState, build_graph
from src.logging import configure_logging

logger = logging.getLogger("defi_agent")

# Configure logging at import time for the API process
configure_logging("human")


RAW_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:15432/defi")
DB_URL = RAW_URL.replace("postgresql+asyncpg://", "postgresql://", 1)  # strip SQLAlchemy suffix

pool = AsyncConnectionPool(
    DB_URL,
    open=False,  # we open it later
    kwargs={
        "autocommit": True,  # DDL must be visible to other sessions
        "row_factory": dict_row,  # AsyncPostgresSaver expects dict rows
    },
    min_size=1,
    max_size=10,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application's lifespan, including the database connection pool."""
    await pool.open()
    await pool.wait()  # optional: pre-warm min_size conns

    async with AsyncPostgresSaver.from_conn_string(DB_URL) as checkpointer:
        await checkpointer.setup()  # creates checkpoints table safely

        app.state.pool = pool
        app.state.checkpointer = checkpointer
        yield
        await pool.close()


app = FastAPI(title="DeFi Risk Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory registry of running tasks
tasks: dict[str, dict[str, Any]] = {}


def _start_job(
    request: Request, address: str, model: str = "gpt-4o", temperature: float = 0.0
):
    """Prepare structures to run a job in the background coroutine."""
    task_id = str(uuid4())
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    tasks[task_id] = {
        "queue": queue,
        "done": False,
        "error": None,
    }

    async def _runner():
        try:
            checkpointer = request.app.state.checkpointer
            init_state = AgentState(
                input_address=address,
                turn_count=0,
                max_turns=10,
                max_messages=7,
                model_name=model,
                temperature=temperature,
            )
            app_graph = build_graph(
                model=model,
                temperature=temperature,
                checkpointer=checkpointer,
            )
            cfg = RunnableConfig(configurable={"thread_id": task_id})
            final_state: dict[str, Any] | None = None
            async for state_dict in app_graph.astream(
                init_state, cfg, stream_mode="values"
            ):
                # Keep reference to the latest state so we can inspect it after the loop
                final_state = state_dict
                # Try to detect the next tool(s) that the AI wants to call so the
                # frontend can show richer progress.
                next_tools: list[str] = []
                try:
                    msgs = state_dict.get("messages", [])
                    if msgs:
                        last_msg = msgs[-1]
                        # Depending on (de)serialisation round-trips, the message can
                        # either be a dict (after JSON round-trip) or an actual
                        # BaseMessage instance.  Handle both.
                        tc_list = None
                        if isinstance(last_msg, dict):
                            tc_list = last_msg.get("tool_calls")
                        else:
                            tc_list = getattr(last_msg, "tool_calls", None)
                        if tc_list:
                            next_tools = [tc.get("name") for tc in tc_list if tc]
                except Exception:
                    # Don't let telemetry collection break the main loop.
                    pass

                payload = {
                    "turn": state_dict.get("turn_count"),
                    "metrics": state_dict.get("metrics", []),
                    "next_tools": next_tools,
                }
                await queue.put({"type": "progress", "payload": payload})

            # If we have a final state try to extract the risk assessment JSON from the last message
            if final_state is not None:
                try:
                    messages = final_state.get("messages", [])
                    if messages:
                        # The last message added by node_finalize contains the JSON string
                        last_msg = messages[-1]
                        # Depending on serialization, it can be a dict or BaseMessage-like object
                        content = last_msg.get("content") if isinstance(last_msg, dict) else getattr(last_msg, "content", None)
                        if content:
                            risk_json = json.loads(content)
                            await queue.put({"type": "result", "payload": risk_json})
                except Exception as exc:
                    logger.warning("Failed to extract final result JSON: %s", exc)

            await queue.put({"type": "done"})
        except Exception as exc:
            logger.exception("Job %s failed", task_id)
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            tasks[task_id]["done"] = True

    asyncio.create_task(_runner())
    return task_id


@app.post("/run")
async def run_job(request: Request, payload: dict[str, Any]):
    address = payload.get("address")
    if not address:
        raise HTTPException(status_code=400, detail="'address' is required")
    model = payload.get("model", "gpt-4o")
    temperature = float(payload.get("temperature", 0.0))
    task_id = _start_job(
        request=request, address=address, model=model, temperature=temperature
    )
    return JSONResponse({"task_id": task_id})


async def _event_generator(task_id: str) -> AsyncGenerator[str, None]:
    if task_id not in tasks:
        yield "event: error\ndata: Task not found\n\n"
        return
    queue: asyncio.Queue[dict[str, Any]] = tasks[task_id]["queue"]
    while True:
        message = await queue.get()
        if message["type"] == "progress":
            data = json.dumps(message["payload"], default=str)
            yield f"event: progress\ndata: {data}\n\n"
        elif message["type"] == "result":
            data = json.dumps(message["payload"], default=str)
            yield f"event: result\ndata: {data}\n\n"
        elif message["type"] == "done":
            yield "event: done\n\n"
            break
        elif message["type"] == "error":
            yield f"event: error\ndata: {message['message']}\n\n"
            break
        
        # Force a flush of the stream to avoid buffering issues
        await asyncio.sleep(0.01)


@app.get("/events/{task_id}")
async def events(task_id: str, request: Request):
    async def _wrap_gen():
        try:
            async for chunk in _event_generator(task_id):
                # Client disconnected?
                if await request.is_disconnected():
                    break
                yield chunk
        finally:
            # Clean up finished tasks
            if task_id in tasks and tasks[task_id]["done"]:
                tasks.pop(task_id, None)

    return StreamingResponse(_wrap_gen(), media_type="text/event-stream")
