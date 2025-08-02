import inspect
import json
import logging
import operator
from pprint import pformat
from typing import Annotated, Any, Callable, Dict, List, Set, TypedDict

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool

class StopNowMessage(BaseMessage):
    """A message to signal that the agent should stop."""
    type: str = "stop_now"
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field, PrivateAttr

from src.utils import get_prompts_dir

logger = logging.getLogger("defi_agent")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# ───────────── 1. portable ToolExecutor import (with shim) ────────────────

try:
    from langgraph.prebuilt.tool_executor import ToolExecutor  # type: ignore
except ImportError:  # older version / missing module

    class ToolExecutor:  # type: ignore
        """Tiny substitute that supports .invoke()."""

        def __init__(self, tools: List[Callable]):
            self._tools = {t.name: t for t in tools}

        def invoke(self, call_spec: Dict[str, Any]):
            name, args = call_spec["name"], call_spec.get("arguments", {})
            tool = self._tools[name]
            if isinstance(tool, BaseTool):  # type: ignore
                return tool.invoke(args)
            return tool(**args)


# TOOLS


# utils
from src.agent_utils import *

# metrics
from src.metrics.liquidity import *

# api calls
from src.providers.alchemy import *
from src.providers.coingecko import *
from src.providers.dexscreener import *
from src.providers.ethplorer import *
from src.providers.goplus import *
from src.providers.moralis import *

TOOLS = [
    api_alchemy_tx_history,
    api_alchemy_portfolio,
    api_coingecko_coin_data,
    api_coingecko_contract,
    api_dexscreener_token_data,
    api_ethplorer_token_data,
    api_goplus_token_security,
    api_moralis_wallet_history,
    api_moralis_wallet_portfolio,
    metric_calculate_exotic_asset_exposure,
    metric_calculate_portfolio_concentration,
    util_stop_now,
    util_wait_five_seconds,
    util_multiply_numbers,
    util_sum_numbers,
    util_divide_numbers,
    util_subtract_numbers,
]

METRIC_OUTPUTS = [
    inspect.signature(tool.func).return_annotation
    for tool in TOOLS
    if tool.name.startswith("metric_")
]

METRIC_NAMES = [m.model_fields["metric_name"].default for m in METRIC_OUTPUTS]

tool_executor = ToolExecutor(TOOLS)

class AgentState(BaseModel):
    input_address: str
    input_request: str
    messages: List[BaseMessage] = Field(default_factory=list)
    metrics: List[BaseModel] = Field(default_factory=list)
    logs: List[str] = Field(default_factory=list)
    turn_count: int = 0
    max_turns: int
    max_messages: int
    llm_with_tools: Any = None  # Will be populated by the setup_llm node

    class Config:
        # Allow non-serializable types like the LLM object
        arbitrary_types_allowed = True


def node_llm(state: AgentState) -> Dict[str, Any]:
    with open(get_prompts_dir() + "/system.md") as f:
        system_prompt = f.read()
    with open(get_prompts_dir() + "/convo.md") as f:
        convo_template = f.read()
    convo_prompt = convo_template.format(
        input_request=state.input_request,
        input_address=state.input_address,
    )
    
    # Keep only the last max_messages, ensuring we don't split tool calls from their results
    messages_to_keep = []
    # Start from the end of the messages
    for msg in reversed(state.messages):
        messages_to_keep.insert(0, msg)
        # If we have enough messages and the last one is not a tool message, we can stop
        if len(messages_to_keep) >= state.max_messages and not isinstance(msg, ToolMessage):
            # However, we need to make sure the AI message that preceded it is included
            if isinstance(msg, AIMessage) and msg.tool_calls:
                pass # This is the start of a tool sequence, keep it
            else:
                break
    
    messages = messages_to_keep

    if not state.messages:
        convo = [
            SystemMessage(system_prompt),
            HumanMessage(content=convo_prompt),
        ]
    else:
        convo = [SystemMessage(system_prompt)] + messages

    logger.info(
        f"Turn {state.turn_count}/{state.max_turns}: Sending {len(convo)} messages to LLM",
    )
    # The [m.content[:80] for m in convo] part is for brevity in logs
    logger.debug("LLM→ messages: %s", [m.content[:80] for m in convo])
    ai_msg: AIMessage = state.llm_with_tools.invoke(convo)  # type: ignore
    logger.info("LLM← tool_calls: %s", ai_msg.tool_calls)
    return {
        "messages": state.messages + [ai_msg], 
        "logs": state.logs + ["AI decided tool calls"], 
        "turn_count": state.turn_count + 1,
    }


def node_tools(state: AgentState) -> Dict[str, Any]:
    ai_msg: AIMessage = state.messages[-1]
    out_messages: List[BaseMessage] = []
    new_metrics: List[BaseModel] = []
    new_logs: List[str] = []

    for tc in ai_msg.tool_calls:
        name, call_id = tc["name"], tc["id"]
        args = tc.get("args") or tc.get("arguments") or {}
        logger.info("Executing %s args=%s", name, args)
        try:
            result = tool_executor.invoke({"name": name, "arguments": args})
            logger.info("→ %s", pformat(result))
            new_logs.append(f"{name} ok")
            if isinstance(result, StopNow):
                out_messages.append(StopNowMessage(content=""))
                # Stop processing further tools in this turn
                break
            is_metric = False
            for mo in METRIC_OUTPUTS:
                if isinstance(result, mo):
                    is_metric = True
                    break
            if is_metric:
                new_metrics.append(result)
                out_messages.append(
                    ToolMessage(content=result.model_dump_json(), tool_call_id=call_id)
                )
            else:
                out_messages.append(
                    ToolMessage(content=json.dumps(result), tool_call_id=call_id)
                )
        except Exception as exc:
            logger.warning("%s error: %s", name, exc)
            new_logs.append(f"{name} error {exc}")
            out_messages.append(ToolMessage(content=f"Tool error: {exc}", tool_call_id=call_id))

    return {
        "messages": state.messages + out_messages, 
        "logs": state.logs + new_logs,
        "metrics": state.metrics + new_metrics,
    }


def decide_next(state: AgentState) -> str:
    if state.turn_count > state.max_turns:
        logger.info("Max turns reached, summarizing.")
        return "summarize"
    
    last_message = state.messages[-1]
    if isinstance(last_message, StopNowMessage):
        logger.info("StopNow signal received, ending.")
        return "end"
        
    produced = {m.metric_name for m in state.metrics}
    if produced.issuperset(METRIC_NAMES):
        logger.info("All metrics produced, summarizing.")
        return "summarize"
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
        
    logger.info("No more tool calls, ending.")
    return "end"


class RiskSummaryOutput(BaseModel):
    risk_score: float = Field(ge=0, le=100)
    justification: str


def node_summarize(state: AgentState) -> Dict[str, Any]:
    metrics_blob = "\n".join(m.model_dump_json() for m in state.metrics)
    with open(get_prompts_dir() + "/risk.md") as f:
        template_prompt = f.read()
    prompt = template_prompt.format(metrics_blob=metrics_blob)
    
    # Use the same model as the main agent
    llm = state.llm_with_tools
    raw_msg: AIMessage = llm.invoke(
        [SystemMessage(prompt)]
    )  # type: ignore

    raw = raw_msg.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        validated = RiskSummaryOutput(**json.loads(raw))
        final_json = validated.model_dump_json()
        logger.info("Validated summary: %s", final_json)
    except Exception as exc:  # demo: broad catch
        final_json = json.dumps({"error": f"Failed to validate: {exc}", "raw": raw})
        logger.warning("Validation failed: %s", exc)

    return {"messages": state.messages + [AIMessage(content=final_json)]}


def build_graph(model: str, temperature: float):
    llm_core = ChatOpenAI(model=model, temperature=temperature, streaming=False)
    llm_with_tools = llm_core.bind_tools(TOOLS)
    
    graph = StateGraph(AgentState)
    
    # This node will be the entry point, ensuring the LLM is always in the state
    def setup_llm(state: AgentState) -> Dict[str, Any]:
        return {"llm_with_tools": llm_with_tools}

    graph.add_node("setup", setup_llm)
    graph.add_node("agent", node_llm)
    graph.add_node("action", node_tools)
    graph.add_node("summarize", node_summarize)

    graph.set_entry_point("setup")
    graph.add_edge("setup", "agent")
    
    graph.add_conditional_edges(
        "agent",
        decide_next,
        {"continue": "action", "summarize": "summarize", "end": END},
    )
    graph.add_edge("action", "agent")
    app = graph.compile()
    return app
