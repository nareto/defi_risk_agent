import functools
from collections import deque, defaultdict
import time

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
                    print(f"Rate limit reached for {func.__name__}. Waiting for {time_to_wait:.2f} seconds.")
                    time.sleep(time_to_wait)
            
            # Record the new call timestamp and execute the function.
            API_CALL_TIMESTAMPS_BY_FUNC[func].append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator