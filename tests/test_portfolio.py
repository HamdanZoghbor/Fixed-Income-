from datetime import date, timedelta
import pytest
import math
from dataclasses import dataclass
from quantlab.fixed_income.portfolio import Position, Portfolio

# import sys
# from pathlib import Path

# # Add project root to Python path dynamically
# sys.path.insert(0, str(Path(_file_).resolve().parent.parent))
class FlatCurve:
    def __init__(self, rate: float, valuation_date: date):
        self._zeros = {valuation_date: rate}
        self.valuation_date = valuation_date
        self.rate = rate

    @classmethod
    def from_zero_rates(cls, valuation_date, zero_rates):
        rate = next(iter(zero_rates.values()))
        return cls(rate, valuation_date)

    def df(self, at_date: date) -> float:
        t = (at_date - self.valuation_date).days / 365
        return math.exp(-self.rate * t)

@dataclass
class DummyInstrument:
    pv: float
    def price(self, curve, valuation_date): return self.pv

@dataclass
class SingleCashflow:
    amount: float
    pay_date: date
    def price(self, curve: FlatCurve, valuation_date: date):
        return self.amount * curve.df(self.pay_date)

def test_pv_sums_linearly():
    c = FlatCurve(0.02, date(2025,1,1))
    p = Portfolio([
        Position(DummyInstrument(100), 2, "LONG"),
        Position(DummyInstrument(50), 1, "SHORT"),
    ])
    assert p.pv(c, c.valuation_date) == 2*100 - 1*50

def test_dv01_sign_and_magnitude():
    val = date(2025,1,1)
    c = FlatCurve(0.02, val)
    pay = val + timedelta(days=365)
    inst = SingleCashflow(100, pay)
    port = Portfolio([Position(inst, 1, "LONG")])
    dv01 = port.dv01(c, val)
    assert dv01 > 0      
    assert dv01 < 200      
