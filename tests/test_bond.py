import pytest
from datetime import date
from quantlab.fixed_income.curve import DiscountCurve
from quantlab.fixed_income.bond import Bond
from quantlab.fixed_income.exceptions import BondValidationError


@pytest.fixture
def sample_bond():
    """Fixture for a standard semi-annual bond."""
    return Bond(
        issue_date=date(2024, 1, 1),
        maturity_date=date(2027, 1, 1),
        zero_rate=0.03,
        coupon_rate=0.05,
        frequency=2,
        face=100.0
    )


def test_invalid_dates():
    """Bond with maturity before issue should raise an error."""
    with pytest.raises(BondValidationError):
        Bond(
            issue_date=date(2025, 1, 1),
            maturity_date=date(2024, 1, 1),
            zero_rate=0.03,
            coupon_rate=0.05,
            frequency=2
        )


def test_invalid_coupon_rate():
    """Negative coupon should raise error."""
    with pytest.raises(BondValidationError):
        Bond(
            issue_date=date(2024, 1, 1),
            maturity_date=date(2026, 1, 1),
            zero_rate=0.03,
            coupon_rate=-0.02,
            frequency=2
        )


def test_invalid_frequency():
    """Unsupported coupon frequency should raise error."""
    with pytest.raises(BondValidationError):
        Bond(
            issue_date=date(2024, 1, 1),
            maturity_date=date(2026, 1, 1),
            zero_rate=0.03,
            coupon_rate=0.04,
            frequency=3
        )


def test_coupon_dates(sample_bond):
    """Coupon dates should be spaced correctly."""
    dates = sample_bond._get_all_coupon_dates()
    assert len(dates) > 2
    assert dates[0] == date(2024, 1, 1)
    assert dates[-1] == date(2027, 1, 1)
    # Check semiannual spacing
    for i in range(1, len(dates)):
        diff_months = (dates[i].year - dates[i-1].year) * 12 + (dates[i].month - dates[i-1].month)
        assert diff_months in [6, 12]  # semi-annual step


def test_cashflows(sample_bond):
    """Ensure correct number and structure of cashflows."""
    cfs = sample_bond.cashflows(date(2025, 1, 1))
    assert all(isinstance(d, tuple) and len(d) == 2 for d in cfs)
    assert cfs[-1][0] == date(2027, 1, 1)
    assert abs(cfs[-1][1] - (sample_bond.face * sample_bond.coupon_rate / sample_bond.frequency + 100)) < 1e-6


def test_accrued_interest(sample_bond):
    """Accrued interest should increase linearly between coupon dates."""
    accr1 = sample_bond.accrued(date(2024, 7, 1))
    accr2 = sample_bond.accrued(date(2024, 10, 1))
    assert accr2 > accr1  # Should accumulate
    assert accr1 >= 0
    assert accr2 <= sample_bond.face * sample_bond.coupon_rate / sample_bond.frequency


def test_price(sample_bond):
    """Test bond pricing via the discount curve."""
    curve = DiscountCurve.from_zero_rates(date(2025, 1, 1), sample_bond.PILLAR_DATES)
    price_clean = sample_bond.price(curve, date(2025, 1, 1), clean=True)
    price_dirty = sample_bond.price(curve, date(2025, 1, 1), clean=False)
    assert price_dirty > price_clean  # Dirty includes accrued interest
    assert price_clean > 90 and price_clean < 110


def test_ytm_convergence(sample_bond):
    """Test that YTM converges for a known price."""
    valuation_date = date(2025, 1, 1)
    curve = DiscountCurve.from_zero_rates(valuation_date, sample_bond.PILLAR_DATES)
    clean_price = sample_bond.price(curve, valuation_date, clean=True)
    ytm = sample_bond.yield_to_maturity(clean_price, valuation_date, is_dirty=False)
    assert 0 <= ytm <= 0.1  # Reasonable range


def test_from_quote_classmethod():
    """Ensure from_quote constructs a bond with computed YTM."""
    valuation_date = date(2025, 1, 1)
    bond = Bond.from_quote(
        clean_price=98.5,
        valuation_date=valuation_date,
        issue_date=date(2024, 1, 1),
        maturity_date=date(2026, 1, 1),
        zero_rate=0.03,
        coupon_rate=0.05,
        frequency=2
    )
    assert bond.ytm is not None
    assert bond.ytm > 0
