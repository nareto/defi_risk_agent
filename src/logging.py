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
        handler = RichHandler(rich_tracebacks=True)

    root.addHandler(handler)
