class CurveConstructionError(Exception):
    """Raised when a DiscountCurve cannot be properly constructed due to invalid input."""
    def __init__(self, message: str):
        super().__init__(f"CurveConstructionError: {message}")

class InterpolationError(Exception):
    """Raised when discount factor interpolation or extrapolation fails."""
    def __init__(self, message: str):
        super().__init__(f"InterpolationError: {message}")

class BondValidationError(Exception):
    """Custom exception for invalid bond parameters."""
    pass