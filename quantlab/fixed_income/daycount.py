from datetime import date

ACT_365F = "ACT/365F"
ACT_ACT = "ACT/ACT"
THIRTY_360 = "30/360"

def year_fraction(d1: date, d2: date, convention: str = ACT_365F) -> float:
    """
    Compute the year fraction between two dates according to the given day count convention.
    """
    if d2 < d1:
        raise ValueError("d2 must be on or after d1")

    if convention == ACT_365F:
        return (d2 - d1).days / 365.0

    elif convention == ACT_ACT:
        # Actual days divided by average year length
        return (d2 - d1).days / 365.25

    elif convention == THIRTY_360:
        d1_day = min(d1.day, 30)
        d2_day = min(d2.day, 30)
        return ((d2.year - d1.year) * 360 +
                (d2.month - d1.month) * 30 +
                (d2_day - d1_day)) / 360.0

    else:
        raise ValueError(f"Unsupported day count convention: {convention}")
