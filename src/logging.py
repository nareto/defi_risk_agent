import json, logging, sys
from types import FrameType
from typing import Any, Dict
from rich.logging import RichHandler
class JsonFormatter(logging.Formatter):
    """Turn a LogRecord into a single-line JSON object."""
    def format(self, record: logging.LogRecord) -> str:          # :contentReference[oaicite:4]{index=4}
        log: Dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "lvl": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "func": record.funcName,
        }
        if record.exc_info:
            log["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log)

def configure_logging(fmt: str = "human", *, level: int = logging.INFO) -> None:
    """
    Configure logging.

    Args:
        fmt: 'human' for coloured pretty logs, 'json' for structured logs.
        level: The logging level to set, e.g., logging.INFO.
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    if fmt == "json":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
    else:
        handler = RichHandler(
            rich_tracebacks=True,
            show_path=False,
            show_level=False,
            show_time=False,
        )
    root.addHandler(handler)
    # Quiet down noisy third-party libraries so that our own DEBUG output is
    # readable even when the root logger is set to DEBUG via --verbose.
    for noisy_logger in (
        "httpx",  # HTTP client used by OpenAI/other providers
        "httpcore",  # lower-level transport layer used by httpx
        "openai",  # OpenAI Python SDK
        "openai._base_client",  # OpenAI internal client traces
    ):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
    # Ensure our own library logger bubbles up to the root handler so its INFO
    # and DEBUG lines are actually emitted.
    logging.getLogger("defi_agent").propagate = True
