"""defi_risk_agent.py – self‑contained LangGraph demo with verbose logging

This revision fixes repeated returns, ensures successful mock data flow, and
adds detailed print‑based logging so you can watch every decision the agent
makes.  Tested with LangGraph 0.6.2, LangChain 0.3.27, and Python 3.13.
"""

import json
import operator
from pprint import pformat
from typing import Annotated, Any, Callable, Dict, List, Set, TypedDict

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import tool, BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

# ===========================================================================
# 0.  ToolExecutor import (portable) – and a shim that calls .invoke()
# ===========================================================================

try:
    from langgraph.prebuilt.tool_executor import ToolExecutor  # type: ignore
except ImportError:  # LangGraph < 0.3.x or other install

    class ToolExecutor:  # type: ignore
        """Very small subset of the real executor (invoke only)."""

        def __init__(self, tools: List[Callable]):
            self._tools = {t.name: t for t in tools}

        def invoke(self, call_spec: Dict[str, Any]):
            name: str = call_spec["name"]
            args: Dict[str, Any] = call_spec.get("arguments") or {}
            tool_obj = self._tools[name]
            # Newer BaseTool objects expose .invoke(); raw callables don’t.
            if isinstance(tool_obj, BaseTool):  # type: ignore
                return tool_obj.invoke(args)  # type: ignore[arg-type]
            return tool_obj(**args)  # fall back to plain fn call

# ===========================================================================
# 1.  Typed metric models
# ===========================================================================

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
    """Final analyst‑style wallet risk assessment."""

    risk_score: float = Field(ge=0, le=100, description="0 (no risk) – 100 (max risk)")
    justification: str



# ===========================================================================
# 2.  Tools – API mocks + metric calculators
# ===========================================================================

@tool
def api_provider1_get_wallet_holdings(address: str) -> Dict[str, Any]:
    """Mock provider 1 – always fails (simulating downtime)."""

    raise ConnectionError("Provider 1 API is down")


@tool
def api_provider2_get_wallet_holdings(address: str) -> Dict[str, Any]:
    """Mock provider 2 – returns a static wallet snapshot."""

    print("[LOG] provider2 returning mock wallet holdings")
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
    """Return dummy market‑cap ranks for requested symbols."""

    print(f"[LOG] market‑data mock called for: {symbols}")
    mapping = {"WETH": 2, "PEPE": 95}
    return {s: {"rank": mapping.get(s)} for s in symbols}


@tool
def metric_calculate_exotic_asset_exposure(
    data: ExoticAssetExposureInput,
) -> ExoticAssetExposureOutput:
    """Percent of USD value in assets ranked > 200 or unranked."""

    total = sum(a.usd_value for a in data.assets)
    if total == 0:
        return ExoticAssetExposureOutput(percentage_exposure=0, description="Wallet empty")
    exotic_val = sum(
        a.usd_value for a in data.assets if a.market_cap_rank is None or a.market_cap_rank > 200
    )
    pct = exotic_val / total * 100
    return ExoticAssetExposureOutput(
        percentage_exposure=pct,
        description=f"{pct:.2f}% of portfolio is in assets ranked >200 or unranked.",
    )


@tool
def metric_calculate_portfolio_concentration(
    data: PortfolioConcentrationInput,
) -> PortfolioConcentrationOutput:
    """Herfindahl‑Hirschman Index (0 diversified ⟶ 1 concentrated)."""

    total = sum(data.asset_values)
    if total == 0:
        return PortfolioConcentrationOutput(hhi_score=0)
    hhi = sum((v / total) ** 2 for v in data.asset_values)
    return PortfolioConcentrationOutput(hhi_score=hhi)


# ===========================================================================
# 3.  Agent state + constants
# ===========================================================================

class AgentState(TypedDict):
    input_address: str
    input_request: str
    messages: Annotated[List[BaseMessage], operator.add]
    metrics: Annotated[List[BaseModel], operator.add]

EXPECTED_METRICS: Set[str] = {
    "Exotic & Unproven Asset Exposure",
    "Portfolio Concentration Index (HHI)",
}

# ===========================================================================
# 4.  LLM and executor setup
# ===========================================================================

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
    "You are a DeFi‑risk agent. 1) Decide which metric_* tools are needed. 2) "
    "Gather data with api_* calls. 3) Build Pydantic inputs and call metric_* "
    "tools. If api_provider1_* fails, switch to provider2_* automatically. 4) "
    "Stop after all metrics are produced."
)

# ===========================================================================
# 5.  Graph nodes with logging
# ===========================================================================

def node_llm(state: AgentState) -> Dict[str, Any]:
    """Brain – requests tool calls."""

    conv: List[BaseMessage]
    if not state["messages"]:
        conv = [
            SystemMessage(SYSTEM_PROMPT),
            HumanMessage(content=f"{state['input_request']} for wallet {state['input_address']}")
        ]
    else:
        conv = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]

    print("\n[LOG] === LLM conversation sent ===")
    for m in conv:
        role = m.__class__.__name__[:3].upper()
        snippet = m.content[:120] if hasattr(m, "content") else str(m)[:120]
        print(f"{role}: {snippet}")
    print("[LOG] === end conversation ===\n")

    ai_out: AIMessage = llm_with_tools.invoke(conv)  # type: ignore
    print("[LOG] LLM decided tool_calls:", ai_out.tool_calls)
    return {"messages": [ai_out]}


def node_tools(state: AgentState) -> Dict[str, Any]:
    """Execute all tool calls, translating 'args'→'arguments' for executor."""

    ai_msg: AIMessage = state["messages"][-1]
    out: List[BaseMessage] = []
    new_metrics: List[BaseModel] = []

    for tc in ai_msg.tool_calls:
        name, call_id = tc["name"], tc["id"]
        # OpenAI returns key "args" whereas LangGraph's executor expects "arguments".
        call_spec = {
            "name": name,
            "arguments": tc.get("args") or tc.get("arguments") or {},
        }
        print(f"[LOG] Executing tool: {name}  id={call_id}  args={call_spec['arguments']}")
        try:
            result = tool_executor.invoke(call_spec)
            print("[LOG] → result:", pformat(result))
            if isinstance(result, (ExoticAssetExposureOutput, PortfolioConcentrationOutput)):
                new_metrics.append(result)
                out.append(ToolMessage(content=result.json(), tool_call_id=call_id))
            else:
                out.append(ToolMessage(content=json.dumps(result), tool_call_id=call_id))
        except Exception as exc:  # pylint: disable=broad-except
            print("[LOG] !!! tool error:", exc)
            out.append(ToolMessage(content=f"Tool error: {exc}", tool_call_id=call_id))

    payload: Dict[str, Any] = {"messages": out}
    if new_metrics:
        payload["metrics"] = new_metrics
    return payload


def decide_next(state: AgentState) -> str:
    obtained = {m.metric_name for m in state["metrics"]}
    last_msg = state["messages"][-1]
    if obtained.issuperset(EXPECTED_METRICS):
        return "summarize"
    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "continue"
    return "end"


def node_summarize(state: AgentState) -> Dict[str, Any]:
    """Call LLM once more and validate it returns JSON with numeric score."""

    metrics_blob = "\n".join(m.json() for m in state["metrics"])
    prompt = (
        "You are an expert DeFi risk analyst. Given these metric JSON blobs, "
        "respond with JSON ONLY containing keys 'risk_score' (number 0‑100) "
        "and 'justification' (string). Strict JSON, no extra keys. \n\n" + metrics_blob
    )
    raw_msg: AIMessage = ChatOpenAI(model="gpt-4o", temperature=0).invoke([SystemMessage(prompt)])  # type: ignore
    raw = raw_msg.content.strip()
    try:
        parsed = json.loads(raw)
        validated = RiskSummaryOutput(**parsed)  # raises if invalid
        final_content = validated.model_dump_json()
        print("[LOG] Final validated summary:", final_content)
    except Exception as exc:  # pylint: disable=broad-except
        final_content = json.dumps({
            "error": f"Failed to parse/validate summary: {exc}",
            "raw": raw,
        })
        print("[LOG] !!! summary validation error", exc)

    return {"messages": [AIMessage(content=final_content)]}

# ===========================================================================
# 6.  Build graph
# ===========================================================================

wf = StateGraph(AgentState)
wf.add_node("agent", node_llm)
wf.add_node("action", node_tools)
wf.add_node("summarize", node_summarize)
wf.set_entry_point("agent")
wf.add_conditional_edges("agent", decide_next, {
    "continue": "action",
    "summarize": "summarize",
    "end": END,
})
wf.add_edge("action", "agent")
app = wf.compile()

# ===========================================================================
# 7. Script entry
# ===========================================================================

if __name__ == "__main__":
    init = {
        "input_address": "0x123…abc",
        "input_request": "Compute exotic exposure and HHI",
        "messages": [],
        "metrics": [],
    }

    final_state = None
    for final_state in app.stream(init, stream_mode="values"):
        pass

    if final_state:
        print("\n=== FINAL RISK SUMMARY ===")
        print(final_state["messages"][-1].content)
