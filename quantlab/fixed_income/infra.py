import time
from functools import wraps
from .exceptions import PortfolioError


def validate_inputs(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for arg in args[1:]:
            if arg is None:
                raise PortfolioError(f"Invalid argument in {func.__name__}")
        return func(*args, **kwargs)
    return wrapper


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = round((time.time() - start) * 1000)
        return {"result": result, "time_ms": elapsed}
    return wrapper
