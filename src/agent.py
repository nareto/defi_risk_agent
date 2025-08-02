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
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field


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

# ─────────────────────────── 2. Pydantic models ───────────────────────────

# ───────────────────────── 4. Agent state & constants ─────────────────────

class AgentState(TypedDict):
    input_address: str
    input_request: str
    messages: Annotated[List[BaseMessage], operator.add]
    metrics: Annotated[List[BaseModel], operator.add]
    logs: Annotated[List[str], operator.add]

EXPECTED_METRICS: Set[str] = {
    "Exotic & Unproven Asset Exposure",
    "Portfolio Concentration Index (HHI)",
}

# TOOLS
from src.providers.alchemy import api_alchemy_tx_history, api_alchemy_portfolio
from src.providers.coingecko import api_coingecko_coin_data, api_coingecko_contract
from src.providers.dexscreener import api_dexscreener_token_data
from src.providers.ethplorer import api_ethplorer_token_data
from src.providers.goplus import api_goplus_token_security
from src.providers.moralis import api_moralis_wallet_history, api_moralis_wallet_portfolio


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
]

tool_executor = ToolExecutor(TOOLS)
llm_core = ChatOpenAI(model="gpt-4o", temperature=0, streaming=False)
llm_with_tools = llm_core.bind_tools(TOOLS)

SYSTEM_PROMPT = (
    "You are a DeFi-risk agent. 1) Decide which metric_* tools are needed. 2) "
    "Gather data with api_* calls. 3) Build Pydantic inputs and call metric_* "
    "tools. If an api_* tool fails, or you hit the rate limit, switch to another api_* tool. 4) "
    "Stop after all metrics are produced or when you can't call anymore api_* tools."
)

# ───────────────────────────── 6. Graph nodes ─────────────────────────────

def node_llm(state: AgentState) -> Dict[str, Any]:
    if not state["messages"]:
        convo = [
            SystemMessage(SYSTEM_PROMPT),
            HumanMessage(content=f"{state['input_request']} for wallet {state['input_address']}"),
        ]
    else:
        convo = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]

    logger.info("LLM→ messages: %s", [m.content[:80] for m in convo])
    ai_msg: AIMessage = llm_with_tools.invoke(convo)  # type: ignore
    logger.info("LLM← tool_calls: %s", ai_msg.tool_calls)
    return {"messages": [ai_msg], "logs": ["AI decided tool calls"]}


def node_tools(state: AgentState) -> Dict[str, Any]:
    ai_msg: AIMessage = state["messages"][-1]
    out: List[BaseMessage] = []
    new_metrics: List[BaseModel] = []
    logs: List[str] = []

    for tc in ai_msg.tool_calls:
        name, call_id = tc["name"], tc["id"]
        args = tc.get("args") or tc.get("arguments") or {}
        logger.info("Executing %s args=%s", name, args)
        try:
            result = tool_executor.invoke({"name": name, "arguments": args})
            logger.info("→ %s", pformat(result))
            logs.append(f"{name} ok")
            if isinstance(result, (ExoticAssetExposureOutput, PortfolioConcentrationOutput)):
                new_metrics.append(result)
                out.append(ToolMessage(content=result.model_dump_json(), tool_call_id=call_id))
            else:
                out.append(ToolMessage(content=json.dumps(result), tool_call_id=call_id))
        except Exception as exc:  # demo: broad catch
            logger.warning("%s error: %s", name, exc)
            logs.append(f"{name} error {exc}")
            out.append(ToolMessage(content=f"Tool error: {exc}", tool_call_id=call_id))

    payload: Dict[str, Any] = {"messages": out, "logs": logs}
    if new_metrics:
        payload["metrics"] = new_metrics
    return payload


def decide_next(state: AgentState) -> str:
    produced = {m.metric_name for m in state["metrics"]}
    last_ai = state["messages"][-1]
    if produced.issuperset(EXPECTED_METRICS):
        return "summarize"
    if isinstance(last_ai, AIMessage) and last_ai.tool_calls:
        return "continue"
    return "end"


def node_summarize(state: AgentState) -> Dict[str, Any]:
    metrics_blob = "\n".join(m.model_dump_json() for m in state["metrics"])
    prompt = (
        "You are an expert DeFi risk analyst. Given these metric JSON blobs, "
        "respond with JSON ONLY containing keys 'risk_score' (number 0-100) "
        "and 'justification' (string). Strict JSON, no extra keys.\n\n" + metrics_blob
    )
    raw_msg: AIMessage = ChatOpenAI(model="gpt-4o", temperature=0).invoke(
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

    return {"messages": [AIMessage(content=final_json)]}

def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", node_llm)
    graph.add_node("action", node_tools)
    graph.add_node("summarize", node_summarize)

    graph.set_entry_point("agent")
    graph.add_conditional_edges(
        "agent", decide_next,
        {"continue": "action", "summarize": "summarize", "end": END},
    )
    graph.add_edge("action", "agent")
    app = graph.compile()
    return app

