from langchain_core.tools import tool
import time
import datetime as dt
from pydantic import BaseModel
from typing import Annotated  
from src.utils import str_to_float

class StopNow(BaseModel):
    pass

@tool
def util_stop_now() -> StopNow:
    """This will stop the program loop. To be used when no progress is being made towards the end goal"""
    return StopNow()

@tool
def util_wait_five_seconds():
    """This will wait for 5 seconds and return. Use it (potentially multiple times) to wait for API rate limits to reset"""
    time.sleep(5)
    return

@tool
def util_math_multiply_numbers(a: str, b: str) -> str:
    """Multiply two floating point numbers in string format (like '3.14' and '2.0'). Return a floating point in string format"""
    return str(str_to_float(a) * str_to_float(b))

@tool
def util_math_sum_numbers(a: str, b: str) -> str:
    """Sum two floating point numbers in string format (like '3.14' and '2.0'). Return a floating point in string format"""
    return str(str_to_float(a) + str_to_float(b))

@tool
def util_math_divide_numbers(a: str, b: str) -> str:
    """Divide two floating point numbers in string format (like '3.14' and '2.0'). Return a floating point in string format"""
    b_float = str_to_float(b)
    if b_float == 0:
        return "Error: Division by zero"
    return str(str_to_float(a) / b_float)


@tool
def util_math_subtract_numbers(a: str, b: str) -> str:
    """Subtract two floating point numbers in string format (like '3.14' and '2.0'). Return a floating point in string format"""
    return str(str_to_float(a) - str_to_float(b))
