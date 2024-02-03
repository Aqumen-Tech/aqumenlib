# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Interest rate swap products, including overnight index swaps (OIS)
"""

from typing import Any, Optional
import pydantic

import QuantLib as ql
from aqumenlib import Date, BusinessDayAdjustment, Frequency, RateIndex
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.namedobject import NamedObject


class InterestRateSwap(pydantic.BaseModel, NamedObject):
    """
    Overnight Index Swap product
    """

    name: str
    index: RateIndex
    effective: Date
    maturity: Date
    frequency: Frequency
    fixed_coupon: float
    float_spread: float = 0.0
    fixed_day_count: DayCount
    payment_calendar: Calendar
    period_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    payment_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    maturity_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    payment_lag: int = 0
    firstCouponDate: Optional[Date] = None
    nextToLastCouponDate: Optional[Date] = None
    endOfMonthFlag: bool = True

    def model_post_init(self, __context: Any) -> None:
        pass

    def get_ql_schedule_fixed(self):
        """
        Generate QuantLib's Schedule object for the fixed leg.
        """
        penult_coupon = self.nextToLastCouponDate.to_ql() if self.nextToLastCouponDate else ql.Date()
        first_coupon = self.firstCouponDate.to_ql() if self.firstCouponDate else ql.Date()
        return ql.Schedule(
            self.effective.to_ql(),
            self.maturity.to_ql(),
            ql.Period(self.frequency.value),
            self.payment_calendar.to_ql(),
            self.period_adjust.value,
            self.maturity_adjust.value,
            ql.DateGeneration.Backward,
            self.endOfMonthFlag,
            first_coupon,
            penult_coupon,
        )

    def get_ql_schedule_floating(self):
        """
        Generate QuantLib's Schedule object for the floating leg.
        """
        penult_coupon = self.nextToLastCouponDate.to_ql() if self.nextToLastCouponDate else ql.Date()
        first_coupon = self.firstCouponDate.to_ql() if self.firstCouponDate else ql.Date()
        if self.index.is_overnight():
            tenor = ql.Period(self.frequency.value)
        else:
            tenor = self.index.tenor.to_ql()
        return ql.Schedule(
            self.effective.to_ql(),
            self.maturity.to_ql(),
            tenor,
            self.payment_calendar.to_ql(),
            self.period_adjust.value,
            self.maturity_adjust.value,
            ql.DateGeneration.Backward,
            self.endOfMonthFlag,
            first_coupon,
            penult_coupon,
        )

    def get_name(self):
        return self.name
