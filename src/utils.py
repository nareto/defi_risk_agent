from tiktoken.core import Encoding


import functools
import time
from collections import defaultdict, deque
from typing import Annotated

import tiktoken


def get_prompts_dir():
    return "src/prompts/"


# A dictionary to store deques of timestamps for each function.
# The key is the function object itself.
API_CALL_TIMESTAMPS_BY_FUNC = defaultdict(deque)


def rate_limit(max_calls: int, period_seconds: int):
    """
    Decorator to enforce a rate limit on function calls.
    This limit is applied on a per-function basis, allowing different
    APIs to have their own independent rate limits.
    Blocks until the call can be made without violating the limit.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the specific deque for the function being called.
            timestamps = API_CALL_TIMESTAMPS_BY_FUNC[func]

            # Remove timestamps older than the defined period.
            now = time.time()
            while timestamps and timestamps[0] < now - period_seconds:
                timestamps.popleft()

            # If the number of calls exceeds the maximum, calculate wait time.
            if len(timestamps) >= max_calls:
                time_to_wait = timestamps[0] + period_seconds - now
                if time_to_wait > 0:
                    print(
                        f"Rate limit reached for {func.__name__}. Waiting for {time_to_wait:.2f} seconds."
                    )
                    time.sleep(time_to_wait)

            # Record the new call timestamp and execute the function.
            API_CALL_TIMESTAMPS_BY_FUNC[func].append(time.time())
            return func(*args, **kwargs)

        from typing import Annotated as _A

        wrapper.__globals__.setdefault("Annotated", _A)
        return wrapper

    return decorator


def str_to_float(value: str) -> float:
    """
    Convert a string representing a number into a Python float.

    Supported formats
    -----------------
    • Standard decimal floats: "123.45", "-0.001"
    • Scientific notation with either ``e`` or Fortran-style ``d`` exponent markers:
      "1.2e3", "3.4d05", "-8.1d-2"
    • Hexadecimal integers, with or without the ``0x`` prefix (case-insensitive):
      "0x1a", "1a", "152d02c7e14af6800000"

    If the string cannot be interpreted, ``ValueError`` is raised.
    """
    import re

    s = value.strip().lower()

    # Handle Fortran-style exponent (replace the first standalone 'd' with 'e')
    if "d" in s and "e" not in s:
        # Convert forms like "1.23d04" -> "1.23e04"
        s = re.sub(r"([0-9])d([+-]?[0-9]+)", r"\1e\2", s)

    # Attempt direct float conversion
    try:
        return float(s)
    except ValueError:
        pass

    # Attempt hexadecimal integer interpretation
    if re.fullmatch(r"(0x)?[0-9a-f]+", s):
        return float(int(s, 16))

    raise ValueError(f"Cannot convert '{value}' to float")


def count_tokens(text: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)


def truncate_to_n_tokens(text: str, model_name: str, max_tokens: int) -> str:
    encoding = tiktoken.encoding_for_model(model_name)
    tokens = encoding.encode(text)
    truncated = tokens[:max_tokens]
    return encoding.decode(truncated)
