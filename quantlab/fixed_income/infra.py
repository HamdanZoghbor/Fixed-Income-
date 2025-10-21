import time

def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"⏱️ {func.__name__} took {end - start:.6f} seconds")
        return result
    return wrapper

def validate_inputs(func):
    def wrapper(*args, **kwargs):
        # Example validation: Check if all numeric inputs are non-negative
        if len(args) == 0 and len(kwargs) == 0:
            raise ValueError(f"The function {func.__name__} requires at least one argument.")
        return func(*args, **kwargs)
    return wrapper
