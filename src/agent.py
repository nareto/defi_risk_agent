import inspect
import json
import logging
from pprint import pformat
from string import Template
from typing import Any, Callable, Dict, List, Optional

import instructor
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
    messages_from_dict,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field, PrivateAttr, field_validator

from src.agent_utils import StopNow
from src.utils import count_tokens, get_prompts_dir, truncate_to_n_tokens

logger = logging.getLogger("defi_agent")


class ToolExecutor:  # type: ignore
    """Tiny substitute that supports .invoke()."""

    def __init__(self, tools: List[Callable]):
        self._tools = {t.name: t for t in tools}

    def invoke(self, call_spec: Dict[str, Any]):
        name, args = call_spec["name"], call_spec.get("arguments", {})
        tool = self._tools[name]
        if isinstance(tool, BaseTool):  # type: ignore
            out = tool.invoke(args)
        else:
            out = tool(**args)
        return out


# TOOLS
# utils
from src.agent_utils import *

# metrics
from src.metrics.liquidity import *
from src.metrics.protocol import *
from src.metrics.systemic import *
from src.metrics.user import *

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
    metric_calculate_low_tvl_protocol_concentration,
    metric_calculate_portfolio_churn_rate,
    metric_calculate_bridged_asset_exposure,
    util_stop_now,
    util_wait_five_seconds,
    util_math_multiply_numbers,
    util_math_sum_numbers,
    util_math_divide_numbers,
    util_math_subtract_numbers,
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
    # messages: List[Union[AIMessage, HumanMessage, SystemMessage, ToolMessage]] = Field(
    #     default_factory=list
    # )
    messages: list[BaseMessage] = Field(default_factory=list)
    # Store metrics as plain dicts so they remain JSON-serialisable across checkpoint
    metrics: List[Dict[str, Any]] = Field(default_factory=list)
    turn_count: int = 0
    max_turns: int
    max_messages: int
    # The bound LLM object should NOT be serialized into checkpoints, because it is
    # not JSON-serialisable and, when re-loaded, becomes a plain dict – which then
    # breaks calls like `.invoke()`.  We therefore exclude it from Pydantic
    # serialisation so it is always rebuilt by the `setup_llm` node when a run
    # (re)starts.
    llm_with_tools: Any = Field(default=None, exclude=True)
    # Store model configuration so we can rebuild the LLM after checkpoint reloads
    model_name: str
    max_token_per_prompt: int = 100000
    max_token_per_msg: Optional[int] = 20000
    temperature: float = 0.0

    class Config:
        # Allow non-serializable types like the LLM object
        arbitrary_types_allowed = True


def node_llm(state: AgentState) -> Dict[str, Any]:
    logger.info(f"─── Turn start: {state.turn_count}/{state.max_turns} " + "─" * 60)
    with open(get_prompts_dir() + "/system.md") as f:
        system_prompt = f.read()
    with open(get_prompts_dir() + "/input.md") as f:
        convo_template = f.read()
    input_prompt = convo_template.format(
        input_address=state.input_address,
    )

    # Keep only the last max_messages, ensuring we don't split tool calls from their results
    messages_to_keep = []
    # Start from the end of the messages
    for msg in reversed(state.messages):
        messages_to_keep.insert(0, msg)
        # If we have enough messages and the last one is not a tool message, we can stop
        if len(messages_to_keep) >= state.max_messages and not isinstance(
            msg, ToolMessage
        ):
            # However, we need to make sure the AI message that preceded it is included
            if isinstance(msg, AIMessage) and msg.tool_calls:
                pass  # This is the start of a tool sequence, keep it
            else:
                break

    messages = messages_to_keep

    def truncate_all_messages_equally(messages: List[BaseMessage]) -> List[str]:
        tot_length = sum(
            [count_tokens(text=str(msg), model=state.model_name) for msg in messages]
        )
        max_msg_tokens = int(state.max_token_per_prompt / len(messages))
        out = [
            truncate_to_n_tokens(
                text=str(msg), model_name=state.model_name, max_tokens=max_msg_tokens
            )
        ]
        return out

    def truncate_long_messages(messages: List[BaseMessage]) -> List[str]:
        out = []
        for msg in messages:
            if state.max_token_per_msg is None:
                out.append(msg)
                continue
            ntokens = count_tokens(text=str(msg), model=state.model_name)
            new_msg = str(msg)
            if ntokens > state.max_token_per_msg:
                new_msg = truncate_to_n_tokens(
                    text=str(msg),
                    model_name=state.model_name,
                    max_tokens=state.max_token_per_msg,
                )
            out.append(new_msg)
        return out

    if not state.messages:
        convo = [
            SystemMessage(system_prompt),
            HumanMessage(content=input_prompt),
        ]
    else:
        # convo = [SystemMessage(system_prompt)] + messages
        # convo = [SystemMessage(system_prompt)] + truncate_all_messages_equally(messages)
        convo = [SystemMessage(system_prompt)] + truncate_long_messages(messages)

    convo_tokens = sum(
        [count_tokens(text=str(msg), model=state.model_name) for msg in convo]
    )

    logger.info(
        f"Invoking LLM with {len(convo)} messages ({convo_tokens} tokens)",
    )
    # logger.info(f"Last 3 messages: %s", [m.content for m in convo[-3:]])

    llm_wt = state.llm_with_tools

    def _needs_rebuild(obj):
        """Return True if obj is clearly not a working RunnableLLM."""
        if obj is None:
            return True
        if isinstance(obj, dict):
            return True
        if not hasattr(obj, "invoke"):
            return True
        # LangChain Runnable has a `.bound` attribute pointing at the core LLM.
        bound = getattr(obj, "bound", None)
        if isinstance(bound, dict):
            return True
        if bound is None or not hasattr(bound, "invoke"):
            return True
        return False

    # If llm_wt is missing or is a plain dict (as happens after JSON deserialisation)
    # we need to reconstruct it.
    if _needs_rebuild(llm_wt):
        logger.debug("Re-creating llm_with_tools after checkpoint load")
        from langchain_openai import ChatOpenAI  # delayed import

        model_name = getattr(state, "model_name", "gpt-4o")
        temperature = getattr(state, "temperature", 0.0)
        llm_core = ChatOpenAI(
            model=model_name, temperature=temperature, streaming=False
        )
        llm_wt = llm_core.bind_tools(TOOLS)
        state.llm_with_tools = llm_wt

    raw_ai_msg: AIMessage = llm_wt.invoke(convo)
    logger.info(
        f"LLM returned {len(raw_ai_msg.tool_calls)} tool calls {raw_ai_msg.tool_calls}"
    )

    ai_msg = AIMessage(
        content=raw_ai_msg.content,
        tool_calls=raw_ai_msg.tool_calls or [],
        invalid_tool_calls=raw_ai_msg.invalid_tool_calls or [],
    )

    return {
        "messages": state.messages + [ai_msg],
        "turn_count": state.turn_count + 1,
        "llm_with_tools": llm_wt,
    }


def node_tools(state: AgentState) -> Dict[str, Any]:
    ai_msg: AIMessage = state.messages[-1]
    out_messages: List[BaseMessage] = []
    new_metrics: List[BaseModel] = []

    for tc in ai_msg.tool_calls:
        name, call_id = tc["name"], tc["id"]
        args = tc.get("args") or tc.get("arguments") or {}
        logger.info("Executing %s args=%s", name, args)
        try:
            result = tool_executor.invoke({"name": name, "arguments": args})
            ntokens = count_tokens(text=str(result), model=state.model_name)
            logger.info(f"Tool {name} returned result ({ntokens} tokens): {result}")
            if isinstance(result, StopNow):
                out_messages.append(
                    ToolMessage(
                        content=json.dumps({"type": "stop_now"}), tool_call_id=call_id
                    )
                )
                break
            is_metric = any(isinstance(result, mo) for mo in METRIC_OUTPUTS)
            if is_metric:
                # Persist as plain dict for easy checkpoint serialisation
                metric_dict = result.model_dump()
                new_metrics.append(metric_dict)
                out_messages.append(
                    ToolMessage(content=json.dumps(metric_dict), tool_call_id=call_id)
                )
            else:
                out_messages.append(
                    ToolMessage(content=json.dumps(result), tool_call_id=call_id)
                )
        except Exception as exc:
            logger.warning("%s error: %s", name, exc)
            logger.info(f"{name} error {exc}")
            out_messages.append(
                ToolMessage(
                    content=json.dumps(
                        {"status": "error", "message": f"Tool failed with error: {exc}"}
                    ),
                    tool_call_id=call_id,
                )
            )

    return {
        "messages": state.messages + out_messages,
        "metrics": state.metrics + new_metrics,
    }


def decide_next(state: AgentState) -> str:
    if state.turn_count + 1 > state.max_turns:
        logger.info("Max turns reached, finalizing.")
        return "finalize"
    last_message = state.messages[-1]
    if isinstance(last_message, ToolMessage):
        try:
            content = json.loads(last_message.content)
            if content.get("type") == "stop_now":
                logger.info("StopNow signal received, finalizing.")
                return "finalize"
        except json.JSONDecodeError:
            pass  # Not a JSON tool message

    def _metric_name(m):
        if isinstance(m, dict):
            return m.get("metric_name")
        return getattr(m, "metric_name", None)

    produced_metrics = {_metric_name(m) for m in state.metrics if _metric_name(m)}
    if produced_metrics.issuperset(METRIC_NAMES):
        logger.info("All metrics produced, finalizing.")
        return "finalize"

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"

    logger.info("No more tool calls, finalizing.")
    return "finalize"


class RiskFinalOutput(BaseModel):
    """Container for the final risk assessment"""

    risk_score: float = Field(
        ge=0,
        le=100,
        description="Global risk score for the wallet, from 0 (very safe investor) to 100 (complete defi degen)",
    )
    justification: str = Field(
        description="A justification in English for the score given"
    )


class RiskFinalOutputWithMetrics(RiskFinalOutput):
    metrics: List[Dict]


def node_finalize(state: AgentState) -> Dict[str, Any]:
    metrics_blob = json.dumps({"data": state.metrics}, indent=2)

    template_prompt = Template(open(get_prompts_dir() + "/risk.md").read())
    prompt = template_prompt.substitute(metrics_blob=metrics_blob)

    logger.info(f"Finalizing, last prompt:\n{prompt}")

    client = instructor.from_provider(f"openai/{state.model_name}")
    output: RiskFinalOutput = client.chat.completions.create(
        response_model=RiskFinalOutput,
        messages=[{"role": "user", "content": prompt}],
    )

    final_output = RiskFinalOutputWithMetrics(
        risk_score=output.risk_score,
        justification=output.justification,
        metrics=state.metrics,
    )
    return {
        "messages": state.messages
        + [AIMessage(content=final_output.model_dump_json(indent=2))]
    }


def build_graph(model: str, temperature: float, checkpointer):
    llm_core = ChatOpenAI(model=model, temperature=temperature, streaming=False)
    llm_with_tools = llm_core.bind_tools(TOOLS)

    graph = StateGraph(AgentState)

    # This node will be the entry point, ensuring the LLM is always in the state
    def setup_llm(state: AgentState) -> Dict[str, Any]:
        # Ensure model configuration is stored in the state so that node_llm can rebuild
        return {
            "llm_with_tools": llm_with_tools,
            "model_name": model,
            "temperature": temperature,
        }

    graph.add_node("setup", setup_llm)
    graph.add_node("agent", node_llm)
    graph.add_node("action", node_tools)
    graph.add_node("finalize", node_finalize)

    graph.set_entry_point("setup")
    graph.add_edge("setup", "agent")

    graph.add_conditional_edges(
        "agent",
        decide_next,
        {"continue": "action", "finalize": "finalize"},
    )
    graph.add_edge("action", "agent")
    app = graph.compile(checkpointer=checkpointer)
    return app
