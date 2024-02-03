# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Bond representation to be used with pricers
"""

from typing import Any, Optional
import pydantic

import QuantLib as ql

from aqumenlib import Date
from aqumenlib.namedobject import NamedObject
from aqumenlib.bond_type import BondType, BondTypeInput
from aqumenlib.term import Term


class Bond(pydantic.BaseModel, NamedObject):
    """
    Class representing an actual traded bond security
    """

    name: str
    bond_type: BondTypeInput
    effective: Date
    maturity: Date
    coupon: Optional[float]
    firstCouponDate: Optional[Date] = None
    nextToLastCouponDate: Optional[Date] = None
    inflation_base: Optional[float] = None
    inflation_lag: Optional[Term] = None
    #
    isin: Optional[str] = None
    issue_name: Optional[str] = None
    ticker: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        penult_coupon = self.nextToLastCouponDate.to_ql() if self.nextToLastCouponDate else ql.Date()
        first_coupon = self.firstCouponDate.to_ql() if self.firstCouponDate else ql.Date()
        self._ql_bond_schedule = ql.Schedule(
            self.effective.to_ql(),
            self.maturity.to_ql(),
            ql.Period(self.bond_type.frequency.value),
            self.bond_type.calendar.to_ql(),
            self.bond_type.period_adjust.value,
            self.bond_type.maturity_adjust.value,
            ql.DateGeneration.Backward,
            self.bond_type.endOfMonthFlag,
            first_coupon,
            penult_coupon,
        )

    def get_name(self):
        return self.name
