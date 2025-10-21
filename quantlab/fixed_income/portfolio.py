from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Mapping, Protocol, runtime_checkable

from .exceptions import PortfolioError
from .infra import validate_inputs 


@runtime_checkable
class PricedInstrument(Protocol):
    def price(self, curve: Any, valuation_date: date) -> float:
        ...

@dataclass
class Position:
    instrument: PricedInstrument
    quantity: float
    side: str = "LONG"

    def signed_quantity(self) -> float:
        if self.side.upper() not in {"LONG", "SHORT"}:
            raise PortfolioError("Side must be LONG or SHORT.")
        if not isinstance(self.quantity, (int, float)):
            raise PortfolioError("Quantity must be a number.")
        return float(self.quantity) if self.side.upper() == "LONG" else -float(self.quantity)

class Portfolio:
    def __init__(self, positions: Iterable[Position]):
        self.positions = list(positions)
        if not self.positions:
            raise PortfolioError("Portfolio cannot be empty.")

    @validate_inputs
    def pv(self, curve: Any, valuation_date: date) -> float:
        total = 0.0
        for pos in self.positions:
            if not isinstance(pos.instrument, PricedInstrument):
                raise PortfolioError("Instrument missing price() method.")
            total += pos.instrument.price(curve, valuation_date) * pos.signed_quantity()
        return total

    @validate_inputs
    def by_instrument_type(self, curve: Any, valuation_date: date) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for pos in self.positions:
            name = pos.instrument.__class__.__name__
            value = pos.instrument.price(curve, valuation_date) * pos.signed_quantity()
            result[name] = result.get(name, 0.0) + value
        return result

    @validate_inputs
    def dv01(self, curve: Any, valuation_date: date, bump_bp: float = 1.0) -> float:
        if bump_bp <= 0:
            raise PortfolioError("bump_bp must be positive.")
        bump_dec = bump_bp * 1e-4
        curve_up, curve_down = _parallel_bump(curve, bump_dec)
        pv_up = self.pv(curve_up, valuation_date)
        pv_dn = self.pv(curve_down, valuation_date)
        return (pv_dn - pv_up) / (2 * bump_dec)


def _extract_zeros(curve: Any) -> Mapping[date, float]:
    if hasattr(curve, "_zeros"):
        zeros = curve._zeros
    elif hasattr(curve, "zeros"):
        zeros = curve.zeros
    else:
        raise PortfolioError("Curve must have zero attribute.")
    if not zeros:
        raise PortfolioError("Curve zeros cannot be empty.")
    return zeros


def _parallel_bump(curve: Any, bump_decimal: float):
    zeros = _extract_zeros(curve)
    val_date = getattr(curve, "valuation_date", None)
    if val_date is None:
        raise PortfolioError("Curve must have valuation_date attribute.")
    up_zeros = {d: r + bump_decimal for d, r in zeros.items()}
    dn_zeros = {d: r - bump_decimal for d, r in zeros.items()}
    CurveClass = curve.__class__
    if not hasattr(CurveClass, "from_zero_rates"):
        raise PortfolioError("Curve class must have from_zero_rates().")
    curve_up = CurveClass.from_zero_rates(valuation_date=val_date, zero_rates=up_zeros)
    curve_dn = CurveClass.from_zero_rates(valuation_date=val_date, zero_rates=dn_zeros)
    return curve_up, curve_dn
