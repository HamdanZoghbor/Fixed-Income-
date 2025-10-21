from datetime import date
from dateutil.relativedelta import relativedelta 
from curve import DiscountCurve
import numpy as np 
from .exceptions import BondValidationError


class Bond:
    def __init__(self, issue_date, maturity_date, zero_rate, coupon_rate, frequency, 
                 face=100.0, day_count='ACT/365', ex_coupon_days=0):
        self.issue_date = issue_date
        self.maturity_date = maturity_date
        self.coupon_rate = coupon_rate
        self.frequency = frequency
        self.face = face
        self.day_count = day_count
        self.ex_coupon_days = ex_coupon_days
        self.PILLAR_DATES = {
                                date(2025, 1, 1): 0.03,
                                date(2026, 1, 1): 0.035,
                                date(2027, 1, 1): 0.04
                            }
                                    
        self.ytm = None 
        self._validate()

    def _validate(self):
        """Helper method to check if the bond's data is valid."""
        if self.maturity_date <= self.issue_date:
            raise BondValidationError("Maturity date must be after issue date")
        if self.coupon_rate < 0:
            raise BondValidationError("Coupon rate cannot be negative")
        if self.frequency not in [1, 2, 4]:
            raise BondValidationError(f"Invalid frequency: {self.frequency}. Must be 1, 2, or 4")
        if self.face <= 0:
            raise BondValidationError("Face value must be positive")

    def _get_all_coupon_dates(self):
        """Helper to generate all coupon dates from maturity backwards."""
        dates = []
        months_step = 12 // self.frequency
        
        current_date = self.maturity_date
        while current_date > self.issue_date:
            dates.append(current_date)
            # Go back by 'months_step' (e.g., 6 months)
            current_date = current_date - relativedelta(months=months_step)
        
        dates.append(self.issue_date)
        return sorted(list(set(dates)))

    def cashflows(self, valuation_date):
        """Calculates all future coupon and principal cashflows."""
        if valuation_date >= self.maturity_date:
            raise BondValidationError("Valuation date is after or on maturity")

        coupon_amount = self.coupon_rate * self.face / self.frequency
        all_dates = self._get_all_coupon_dates()
        
        future_cfs = []
        for d in all_dates:
            if d > valuation_date: # Only include future dates
                cf = coupon_amount
                if d == self.maturity_date:
                    cf += self.face  # Add principal at maturity
                future_cfs.append((d, cf))
                
        return sorted(future_cfs)

    def accrued(self, valuation_date):
        """Calculates the accrued interest on the valuation_date."""
        if valuation_date >= self.maturity_date or valuation_date < self.issue_date:
            return 0.0

        all_dates = self._get_all_coupon_dates()
        coupon_amount = self.coupon_rate * self.face / self.frequency

        prev_coupon_date = self.issue_date
        next_coupon_date = self.maturity_date

        for d in all_dates:
            if d <= valuation_date:
                prev_coupon_date = d
            if d > valuation_date:
                next_coupon_date = d
                break
        
        if valuation_date == prev_coupon_date:
            return 0.0 

        days_in_period = (next_coupon_date - prev_coupon_date).days
        days_accrued = (valuation_date - prev_coupon_date).days
        
        if days_in_period == 0:
            return 0.0

        fraction = days_accrued / days_in_period
        return fraction * coupon_amount

    
    def price(self, curve, valuation_date, clean=True):
        """Returns the bond's price (clean or dirty) using discount factors."""
        all_cashflows = self.cashflows(valuation_date)

        dfs_curve = DiscountCurve.from_zero_rates(valuation_date, self.PILLAR_DATES)
        dfs = np.array([dfs_curve.df(cf_date) for cf_date, _ in all_cashflows])
        cfs = np.array([cf for _, cf in all_cashflows])

        pv = np.sum(dfs * cfs)
        accrued_amt = self.accrued(valuation_date)

        if clean:
            return pv - accrued_amt  
        else:
            return pv  

    def yield_to_maturity(self, price, valuation_date, is_dirty=True):
        """Solves for the Yield to Maturity (YTM) given a market price."""
        
        if is_dirty:
            dirty_price = price
        else:
            dirty_price = price + self.accrued(valuation_date)

        cfs = self.cashflows(valuation_date)
        if not cfs:
            return 0.0

        low_yield = -0.10 
        high_yield = 5.0 
        tolerance = 0.000001
        
        for i in range(1000): 
            mid_yield = (low_yield + high_yield) / 2
            
            price_at_mid = Bond.price_from_ytm(
                mid_yield, cfs, valuation_date, self.frequency
            )
            
            price_diff = price_at_mid - dirty_price
            
            if abs(price_diff) < tolerance:
                return mid_yield # Found it!
            
            elif price_diff > 0: 
                low_yield = mid_yield
            else:
                high_yield = mid_yield
                
        raise ValueError("YTM calculation did not converge.")

    @staticmethod
    def price_from_ytm(ytm, cashflows, valuation_date, frequency):
        pv = 0.0
        days_in_year = 365.25 
        
        for cf_date, cf_amount in cashflows:
            t_days = (cf_date - valuation_date).days
            t_years = t_days / days_in_year
            
            exponent = t_years * frequency
            
            try:
                df = 1.0 / ((1.0 + ytm / frequency) ** exponent)
            except ValueError:
                df = 0.0
            
            pv += cf_amount * df
            
        return pv

    @classmethod
    def from_quote(cls, clean_price, valuation_date, **kwargs):
        bond = cls(**kwargs) 
        
        bond.ytm = bond.yield_to_maturity(
            clean_price, 
            valuation_date, 
            is_dirty=False # The input price was clean
        )
        
        return bond