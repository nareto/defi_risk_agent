import logging
import json
import click
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from src.agent import build_graph, AgentState
from src.logging import configure_logging
from langgraph.checkpoint.sqlite import SqliteSaver
from uuid import uuid4
from langchain_core.runnables import RunnableConfig


logger = logging.getLogger("defi_agent")
console = Console()


@click.command()
@click.argument("address", required=False)
@click.option(
    "-v", "--verbose", is_flag=True, help="Enable verbose output (DEBUG level)."
)
@click.option("-q", "--quiet", is_flag=True, help="Enable quiet output (ERROR level).")
@click.option(
    "--max-turns", type=int, default=10, help="Max turns before forcing summary."
)
@click.option(
    "--max-messages", type=int, default=5, help="Max messages to keep in history."
)
@click.option("--model", type=str, default="gpt-4o", help="OpenAI model to use.")
@click.option(
    "--temperature", type=float, default=0.0, help="OpenAI model temperature."
)
@click.option(
    "--resume-from",
    type=str,
    help="Resume from a checkpoint, e.g., 'thread_id:turn_number'.",
)
@click.option(
    "--log-format",
    type=click.Choice(["human", "json"]),
    default="human",
    help="Log format.",
)
def main(
    address: str,
    verbose: bool,
    quiet: bool,
    max_turns: int,
    max_messages: int,
    model: str,
    temperature: float,
    resume_from: str | None,
    log_format: str,
):
    """DeFi Risk Agent CLI"""
    if quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    configure_logging(log_format, level=log_level)

    with SqliteSaver.from_conn_string("sqlite:runs.db") as checkpointer:
        thread_id: str
        checkpoint_id = None
        if resume_from:
            parts = resume_from.split(":")
            if len(parts) > 2:
                raise click.UsageError(
                    "Invalid format for --resume-from. Use 'thread_id' or 'thread_id:turn_number'."
                )

            thread_id = parts[0]
            if len(parts) == 2:
                try:
                    wanted_turn = int(parts[1])
                except ValueError:
                    raise click.UsageError("Turn number must be an integer.")

                thread_config = RunnableConfig(configurable={"thread_id": thread_id})
                cps = list(checkpointer.list(thread_config))  # newest → oldest
                try:
                    cp = next(
                        cp
                        for cp in cps
                        if cp.checkpoint["channel_values"].get("turn_count")
                        == wanted_turn
                    )
                except StopIteration:
                    raise click.UsageError(
                        f"Turn {wanted_turn} not found (thread has {len(cps)} checkpoints)."
                    )

                # Successfully found checkpoint for desired turn
                checkpoint_id = (
                    cp.config["configurable"].get("checkpoint_id")  # present in ≥0.2.4
                    or cp.checkpoint["id"]  # fallback
                )

            init = None
        else:
            if not address:
                raise click.UsageError("Address is required for a new run.")
            thread_id = str(uuid4())
            init = AgentState(
                input_address=address,
                turn_count=0,
                max_turns=max_turns,
                max_messages=max_messages,
            )

        app = build_graph(
            model=model, temperature=temperature, checkpointer=checkpointer
        )
        config = {"configurable": {"thread_id": thread_id}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id
        cfg = RunnableConfig(**config)

        console.print(
            Panel(
                f"Starting agent with [bold cyan]{model}[/bold cyan] \t Thread: {thread_id}",
                title="🚀 Agent Started",
            )
        )
        final_state = None

        with console.status(
            f"[bold green]Agent is running. Thread: {thread_id}..."
        ) as status:
            for state_dict in app.stream(init, cfg, stream_mode="values"):
                snapshot = AgentState(**state_dict)

                if snapshot.messages:
                    msg = snapshot.messages[-1]
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        logger.debug(f"🤖 AI -> Tools: {str(msg.tool_calls)[:500]} ...")
                    else:
                        logger.debug(f"🛠️ Tools -> AI: {str(msg.content)[:500]} ...")

                if snapshot.metrics:
                    logger.debug(
                        f"📊 Metrics: {snapshot.metrics[-1].__class__.__name__}"
                    )
                final_state = snapshot
                status.update(
                    f"[bold green]Turn {snapshot.turn_count}: Processing...[/bold green]"
                )
        if final_state:
            console.print(
                Panel(
                    f"FINAL RISK SUMMARY (turn {final_state.turn_count})",
                    style="bold red",
                    expand=False,
                )
            )
        if final_state and final_state.messages:
            summary_content = final_state.messages[-1].content
            if isinstance(summary_content, str):
                try:
                    summary_json = json.loads(summary_content)
                    console.print(JSON(json.dumps(summary_json)))
                except (json.JSONDecodeError, TypeError):
                    logger.debug("Could not parse output JSON, printing raw content.")
                    console.print(summary_content)
            else:
                console.print(summary_content)


if __name__ == "__main__":
    main()
