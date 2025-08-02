"""defi_risk_agent.py – LangGraph demo with structured logging & fence-tolerant summary

Tested with:
  • LangGraph 0.6.2
  • LangChain 0.3.27
  • Python 3.13
"""

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
from langchain_core.tools import tool, BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

# ─────────────────────────────── 0. logging ────────────────────────────────

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

class ExoticAsset(BaseModel):
    symbol: str
    usd_value: float
    market_cap_rank: int | None = Field(description="None if unranked")


class ExoticAssetExposureInput(BaseModel):
    assets: List[ExoticAsset]


class ExoticAssetExposureOutput(BaseModel):
    metric_name: str = "Exotic & Unproven Asset Exposure"
    percentage_exposure: float
    description: str


class PortfolioConcentrationInput(BaseModel):
    asset_values: List[float]


class PortfolioConcentrationOutput(BaseModel):
    metric_name: str = "Portfolio Concentration Index (HHI)"
    hhi_score: float


class RiskSummaryOutput(BaseModel):
    risk_score: float = Field(ge=0, le=100)
    justification: str

# ──────────────────────── 3. Tool definitions ─────────────────────────────

@tool
def api_provider1_get_wallet_holdings(address: str) -> Dict[str, Any]:
    """Mock provider that *always* fails to simulate downtime."""
    raise ConnectionError("Provider 1 API is down")


@tool
def api_provider2_get_wallet_holdings(address: str) -> Dict[str, Any]:
    """Mock provider that returns static wallet holdings."""
    logger.info("provider2: returning mock wallet holdings")
    return {
        "wallet": address,
        "tokens": [
            {"symbol": "WETH", "value_usd": 7_000},
            {"symbol": "PEPE", "value_usd": 12.5},
            {"symbol": "UNKNOWN_TKN", "value_usd": 150},
        ],
    }


@tool
def api_get_token_market_data(symbols: List[str]) -> Dict[str, Any]:
    """Return dummy market-cap ranks for a list of symbols."""
    logger.info("market-data mock for %s", symbols)
    ranks = {"WETH": 2, "PEPE": 95}
    return {s: {"rank": ranks.get(s)} for s in symbols}


@tool
def metric_calculate_exotic_asset_exposure(
    data: ExoticAssetExposureInput,
) -> ExoticAssetExposureOutput:
    """Percent USD in assets ranked >200 or unranked."""
    total = sum(a.usd_value for a in data.assets)
    if total == 0:
        return ExoticAssetExposureOutput(percentage_exposure=0, description="Wallet empty")
    exotic_val = sum(
        a.usd_value for a in data.assets if a.market_cap_rank is None or a.market_cap_rank > 200
    )
    pct = exotic_val / total * 100
    return ExoticAssetExposureOutput(
        percentage_exposure=pct,
        description=f"{pct:.2f}% of value in assets ranked >200 or unranked.",
    )


@tool
def metric_calculate_portfolio_concentration(
    data: PortfolioConcentrationInput,
) -> PortfolioConcentrationOutput:
    """Compute the Herfindahl-Hirschman Index (0 diversified → 1 concentrated)."""
    total = sum(data.asset_values)
    if total == 0:
        return PortfolioConcentrationOutput(hhi_score=0)
    hhi = sum((v / total) ** 2 for v in data.asset_values)
    return PortfolioConcentrationOutput(hhi_score=hhi)

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

# ─────────────────────── 5. LLM + executor setup ──────────────────────────

TOOLS = [
    api_provider1_get_wallet_holdings,
    api_provider2_get_wallet_holdings,
    api_get_token_market_data,
    metric_calculate_exotic_asset_exposure,
    metric_calculate_portfolio_concentration,
]

tool_executor = ToolExecutor(TOOLS)
llm_core = ChatOpenAI(model="gpt-4o", temperature=0, streaming=False)
llm_with_tools = llm_core.bind_tools(TOOLS)

SYSTEM_PROMPT = (
    "You are a DeFi-risk agent. 1) Decide which metric_* tools are needed. 2) "
    "Gather data with api_* calls. 3) Build Pydantic inputs and call metric_* "
    "tools. If api_provider1_* fails, switch to provider2_* automatically. 4) "
    "Stop after all metrics are produced."
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

# ───────────────────────────── 7. Build graph ─────────────────────────────

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

# ───────────────────────────── 8. CLI entry ──────────────────────────────

if __name__ == "__main__":
    init = {
        "input_address": "0x123…abc",
        "input_request": "Compute exotic exposure and HHI",
        "messages": [],
        "metrics": [],
        "logs": [],
    }
    for final_state in app.stream(init, stream_mode="values"):
        pass

    print("\n=== FINAL RISK SUMMARY ===")
    print(final_state["messages"][-1].content)
