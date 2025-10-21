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
        for arg in args:
            if isinstance(arg, (int, float)) and arg < 0:
                raise ValueError(f"Invalid input: {arg} is negative")
        for key, value in kwargs.items():
            if isinstance(value, (int, float)) and value < 0:
                raise ValueError(f"Invalid input: {key}={value} is negative")
        return func(*args, **kwargs)
    return wrapper