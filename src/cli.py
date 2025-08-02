import argparse
import logging
import json
from src.agent import build_graph

# Configure logging
logger = logging.getLogger("defi_agent")

def main():
    parser = argparse.ArgumentParser(description="DeFi Risk Agent CLI")
    parser.add_argument("address", help="The wallet address to analyze.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="The maximum number of turns before forcing a summary.",
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        default=5,
        help="Maximum number of messages to keep in history.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o",
        help="The OpenAI model to use.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="The temperature for the OpenAI model.",
    )
    args = parser.parse_args()

    # Set logger level based on verbosity
    if args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.CRITICAL) # Effectively silence logger

    init = {
        "input_address": args.address,
        "input_request": "Compute exotic exposure and HHI",
        "messages": [],
        "metrics": [],
        "logs": [],
        "turn_count": 0,
        "max_turns": args.max_turns,
        "max_messages": args.max_messages,
    }
    app = build_graph(model=args.model, temperature=args.temperature)

    final_state = None
    for state in app.stream(init, stream_mode="values"):
        if args.verbose and state["logs"]:
            print("\n".join(state["logs"][-5:]))
        if args.verbose:
            print("\n" + f"─── Turn {state.get('turn_count', 0)}/{state.get('max_turns', 10)} " + "─" * 60)
            if state.get("messages"):
                msg = state["messages"][-1]
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    print(f"🤖 AI -> Tools: {msg.tool_calls}")
                else:
                    print(f"🛠️ Tools -> AI: {msg.content}")

            if state.get("metrics"):
                print(f"📊 Metrics: {state['metrics'][-1].__class__.__name__}")
        final_state = state

    print("\n\n" + "=" * 25 + " FINAL RISK SUMMARY " + "=" * 25)
    if final_state and "messages" in final_state and final_state["messages"]:
        summary_content = final_state["messages"][-1].content
        try:
            # Try to parse and pretty-print the JSON summary
            summary_json = json.loads(summary_content)
            print(json.dumps(summary_json, indent=2))
        except (json.JSONDecodeError, TypeError):
            # Fallback for non-json or malformed content
            print(summary_content)

if __name__ == "__main__":
    main()
