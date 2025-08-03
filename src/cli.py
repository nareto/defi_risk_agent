import argparse
import logging
import json
from src.agent import build_graph
from src.agent import AgentState
import datetime as dt
import os

# Configure logging
logger = logging.getLogger("defi_agent")


def main():
    parser = argparse.ArgumentParser(description="DeFi Risk Agent CLI")
    parser.add_argument("address", help="The wallet address to analyze.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (DEBUG level).",
    )
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Enable quiet output (ERROR level), overrides verbose.",
    )
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
    parser.add_argument(
        "--resume-from",
        type=str,
        default=None,
        help="Path to a turn JSON file to resume from.",
    )
    parser.add_argument(
        "--log-format",
        choices=["human", "json"],
        default="human",
        help="Choose 'json' for structured logs or 'human' for coloured text.",
    )
    args = parser.parse_args()
    from src.logging import configure_logging

    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    configure_logging(args.log_format, level=log_level)

    if args.resume_from:
        with open(args.resume_from) as f:
            init = AgentState.model_validate_json(f.read())
    else:
        init = AgentState(
            input_address=args.address,
            turn_count=0,
            max_turns=args.max_turns,
            max_messages=args.max_messages,
        )

    app = build_graph(model=args.model, temperature=args.temperature)
    print(f"Starting agent with model: {args.model}")
    final_state = None
    OUTPUT_DIR = f"./runs_output/state_{dt.datetime.now().isoformat()}"
    os.makedirs(OUTPUT_DIR)
    for state in app.stream(init, stream_mode="values"):
        # The state object from the stream is a dict, we want the AgentState object
        # which is available under the 'state_obj' key, inserted by a custom tap.
        # This is a bit of a workaround to get the full state.
        snapshot = state.get("state_obj")
        if not snapshot:
             # Fallback for older versions or different stream configurations
            snapshot_dict = state.copy()
            snapshot_dict.pop('state_obj', None) # Remove if it exists but is None
            # Recreate the state object from the dictionary representation
            snapshot = AgentState(**snapshot_dict)

        with open(f"{OUTPUT_DIR}/turn_{snapshot.turn_count}.json", "w") as f:
            f.write(snapshot.model_dump_json(indent=2))

        logger.info(
            "\n"
            + f"─── Turn {snapshot.turn_count}/{snapshot.max_turns} "
            + "─" * 60
        )
        if snapshot.messages:
            msg = snapshot.messages[-1]
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                logger.debug(f"🤖 AI -> Tools: {str(msg.tool_calls)[:500]} ...")
            else:
                logger.debug(f"🛠️ Tools -> AI: {str(msg.content)[:500]} ...")

        if snapshot.metrics:
            logger.debug(f"📊 Metrics: {snapshot.metrics[-1].__class__.__name__}")
        final_state = snapshot

    logger.info("\n\n" + "=" * 25 + " FINAL RISK SUMMARY " + "=" * 25)
    if final_state and final_state.messages:
        summary_content = final_state.messages[-1].content
        try:
            # Try to parse and pretty-print the JSON summary
            summary_json = json.loads(summary_content)
            print(json.dumps(summary_json, indent=2))
        except (json.JSONDecodeError, TypeError):
            # Fallback for non-json or malformed content
            logger.debug(f"Could not parse malformed output JSON")
            print(summary_content)


if __name__ == "__main__":
    main()
