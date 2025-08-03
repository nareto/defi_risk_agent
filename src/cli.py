import logging
import json
import datetime as dt
import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.json import JSON

from src.agent import build_graph, AgentState
from src.logging import configure_logging

logger = logging.getLogger("defi_agent")
console = Console()

@click.command()
@click.argument("address", required=False)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output (DEBUG level).")
@click.option("-q", "--quiet", is_flag=True, help="Enable quiet output (ERROR level).")
@click.option("--max-turns", type=int, default=10, help="Max turns before forcing summary.")
@click.option("--max-messages", type=int, default=5, help="Max messages to keep in history.")
@click.option("--model", type=str, default="gpt-4o", help="OpenAI model to use.")
@click.option("--temperature", type=float, default=0.0, help="OpenAI model temperature.")
@click.option("--resume-from", type=click.Path(exists=True), help="Resume from a turn JSON file.")
@click.option("--log-format", type=click.Choice(["human", "json"]), default="human", help="Log format.")
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

    if resume_from:
        with open(resume_from) as f:
            init = AgentState.model_validate_json(f.read())
    else:
        if not address:
            raise click.UsageError("Address is required when not resuming from a file.")
        init = AgentState(
            input_address=address,
            turn_count=0,
            max_turns=max_turns,
            max_messages=max_messages,
        )

    app = build_graph(model=model, temperature=temperature)
    console.print(Panel(f"Starting agent with [bold cyan]{model}[/bold cyan]", title="🚀 Agent Started"))

    final_state = None
    output_dir = f"./runs_output/state_{dt.datetime.now().isoformat()}"
    os.makedirs(output_dir)

    with console.status("[bold green]Agent is running...") as status:
        for state_dict in app.stream(init, stream_mode="values"):
            snapshot = AgentState(**state_dict)
            
            with open(f"{output_dir}/turn_{snapshot.turn_count}.json", "w") as f:
                f.write(snapshot.model_dump_json(indent=2))

            logger.info(f"─── Turn {snapshot.turn_count}/{snapshot.max_turns} " + "─" * 60)
            if snapshot.messages:
                msg = snapshot.messages[-1]
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    logger.debug(f"🤖 AI -> Tools: {str(msg.tool_calls)[:500]} ...")
                else:
                    logger.debug(f"🛠️ Tools -> AI: {str(msg.content)[:500]} ...")

            if snapshot.metrics:
                logger.debug(f"📊 Metrics: {snapshot.metrics[-1].__class__.__name__}")
            final_state = snapshot
            status.update(f"[bold green]Turn {snapshot.turn_count}: Processing...[/bold green]")

    console.print(Panel("FINAL RISK SUMMARY", style="bold red", expand=False))
    if final_state and final_state.messages:
        summary_content = final_state.messages[-1].content
        try:
            summary_json = json.loads(summary_content)
            console.print(JSON(json.dumps(summary_json)))
        except (json.JSONDecodeError, TypeError):
            logger.debug("Could not parse output JSON, printing raw content.")
            console.print(summary_content)

if __name__ == "__main__":
    main()
