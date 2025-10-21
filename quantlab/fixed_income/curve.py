from datetime import date
from math import exp, isfinite
from typing import Dict, List
from .exceptions import CurveConstructionError, InterpolationError
from .daycount import year_fraction

class DiscountCurve:
    """
    Deterministic discount curve built from zero rates.
    Supports exponential discounting with continuous compounding.
    """

    def __init__(self, valuation_date: date, pillar_dates: List[date], zero_rates: List[float]):
        if len(pillar_dates) != len(zero_rates):
            raise CurveConstructionError("pillar_dates and zero_rates must have same length.")
        if any(p2 <= p1 for p1, p2 in zip(pillar_dates, pillar_dates[1:])):
            raise CurveConstructionError("pillar_dates must be strictly increasing.")
        if any(not isfinite(r) or r < 0 for r in zero_rates):
            raise CurveConstructionError("zero_rates must be finite and non-negative.")

        self.valuation_date = valuation_date
        self.pillar_dates = pillar_dates
        self.zero_rates = zero_rates

    @classmethod
    def from_zero_rates(cls, valuation_date: date, zero_curve: Dict[date, float]):
        """
        Construct a DiscountCurve from a mapping of {pillar_date: zero_rate}.
        """
        if not zero_curve:
            raise CurveConstructionError("zero_curve mapping cannot be empty.")
        pillar_dates = sorted(zero_curve.keys())
        zero_rates = [zero_curve[d] for d in pillar_dates]
        return cls(valuation_date, pillar_dates, zero_rates)

    @classmethod
    def flat(cls, rate: float, valuation_date: date):
        """
        Convenience constructor for a flat discount curve.
        """
        if rate < 0 or not isfinite(rate):
            raise CurveConstructionError("Flat rate must be finite and non-negative.")
        return cls(valuation_date, [valuation_date], [rate])

    def df(self, at_date: date) -> float:
        """
        Compute the discount factor at a given date using linear interpolation
        on zero rates and continuous compounding.
        """
        if at_date < self.valuation_date:
            raise InterpolationError("Cannot compute discount factor before valuation_date.")

        # Exact match
        if at_date in self.pillar_dates:
            t = year_fraction(self.valuation_date, at_date)
            r = self.zero_rates[self.pillar_dates.index(at_date)]
            return exp(-r * t)

        # Interpolation between pillar points
        for i in range(1, len(self.pillar_dates)):
            d1, d2 = self.pillar_dates[i - 1], self.pillar_dates[i]
            if d1 < at_date < d2:
                t1 = year_fraction(self.valuation_date, d1)
                t2 = year_fraction(self.valuation_date, d2)
                t = year_fraction(self.valuation_date, at_date)
                r1, r2 = self.zero_rates[i - 1], self.zero_rates[i]
                # linear interpolation on zero rate
                r = r1 + (r2 - r1) * (t - t1) / (t2 - t1)
                return exp(-r * t)

        # Extrapolate flat beyond last pillar
        last_rate = self.zero_rates[-1]
        t = year_fraction(self.valuation_date, at_date)
        return exp(-last_rate * t)
