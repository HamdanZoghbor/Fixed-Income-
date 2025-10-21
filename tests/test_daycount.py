import pytest
from datetime import date
from quantlab.fixed_income.daycount import year_fraction

def test_act_365f_basic():
    d1 = date(2025, 1, 1)
    d2 = date(2026, 1, 1)
    yf = year_fraction(d1, d2, convention="ACT/365F")
    assert yf - (d2 - d1).days / 365.0 < 1e-10



def test_thirty_360_end_of_month():
    # Test end-of-month adjustment
    d1 = date(2025, 1, 31)
    d2 = date(2025, 2, 28)
    yf = year_fraction(d1, d2, convention="30/360")
    # 30/360 = 1 month
    assert abs(yf - (30 / 360)) < 1e-2


def test_same_day_zero_fraction():
    d = date(2025, 6, 15)
    assert year_fraction(d, d, "ACT/365F") == 0.0


def test_invalid_convention_raises():
    d1 = date(2025, 1, 1)
    d2 = date(2026, 1, 1)
    with pytest.raises(ValueError):
        year_fraction(d1, d2, "INVALID")
