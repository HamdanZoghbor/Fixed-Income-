import pytest
from datetime import date, timedelta
from math import exp

from quantlab.fixed_income.curve import DiscountCurve, CurveConstructionError, InterpolationError
from quantlab.fixed_income.daycount import year_fraction


def test_flat_curve_discount_factor():
    valuation_date = date(2025, 1, 1)
    curve = DiscountCurve.flat(rate=0.05, valuation_date=valuation_date)

    # 1 year ahead should have df = exp(-0.05 * 1)
    d1 = valuation_date.replace(year=2026)
    t = year_fraction(valuation_date, d1)
    expected_df = exp(-0.05 * t)
    assert abs(curve.df(d1) - expected_df) < 1e-10


def test_from_zero_rates_and_interpolation():
    valuation_date = date(2025, 1, 1)
    zero_curve = {
        date(2025, 7, 1): 0.02,
        date(2026, 1, 1): 0.03,
    }
    curve = DiscountCurve.from_zero_rates(valuation_date, zero_curve)

    # exact pillar check
    df_pillar = curve.df(date(2026, 1, 1))
    t = year_fraction(valuation_date, date(2026, 1, 1))
    assert abs(df_pillar - exp(-0.03 * t)) < 1e-10

    # interpolation (midpoint)
    mid_date = date(2025, 9, 1)
    df_mid = curve.df(mid_date)
    assert 0 < df_mid <= 1


def test_invalid_curve_inputs():
    valuation_date = date(2025, 1, 1)

    # non-increasing pillar dates
    with pytest.raises(CurveConstructionError):
        DiscountCurve(
            valuation_date,
            [date(2025, 1, 1), date(2024, 1, 1)],
            [0.02, 0.03]
        )

    # mismatched lengths
    with pytest.raises(CurveConstructionError):
        DiscountCurve(
            valuation_date,
            [date(2025, 1, 1)],
            [0.02, 0.03]
        )

    # negative rate
    with pytest.raises(CurveConstructionError):
        DiscountCurve(
            valuation_date,
            [date(2026, 1, 1)],
            [-0.01]
        )


def test_df_before_valuation_raises():
    valuation_date = date(2025, 1, 1)
    curve = DiscountCurve.flat(rate=0.05, valuation_date=valuation_date)
    with pytest.raises(InterpolationError):
        curve.df(date(2024, 12, 31))