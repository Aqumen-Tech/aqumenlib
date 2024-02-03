# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Cash-like instruments to be used for calibration
"""

from typing import Any, Optional, List
import pydantic
import QuantLib as ql

from aqumenlib import (
    Currency,
    RiskType,
    AssetClass,
    BusinessDayAdjustment,
    MarketView,
)
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.index import Index
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.instruments.rate_family import RateInstrumentFamily
from aqumenlib.term import Term


class CashDepoFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    Cash deposit or simple money instrument
    """

    name: str
    currency: Currency
    settlement_delay: int
    payment_adjust: BusinessDayAdjustment = BusinessDayAdjustment.FOLLOWING
    day_count: Optional[DayCount] = None
    calendar: Optional[Calendar] = None

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.currency, risk_type=RiskType.RATE, asset_class=AssetClass.RATE
        )
        if self.calendar is None:
            self.calendar = Calendar(ql_calendar_id="NullCalendar")
        if self.day_count is None:
            self.day_count = DayCount.ACT365F

    def get_meta(self) -> InstrumentFamilyMeta:
        return self._inst_meta

    def get_name(self) -> str:
        return self.name

    def get_underlying_indices(self) -> List[Index]:
        return []

    def create_ql_instrument(
        self,
        market: "MarketView",
        quote_handle: ql.RelinkableQuoteHandle,
        term: Term,
        discounting_id: Optional[str] = None,
        target_index: Optional[Index] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
        helper = ql.DepositRateHelper(
            quote_handle,
            term.to_ql(),
            self.settlement_delay,
            self.calendar.to_ql(),
            self.payment_adjust.value,
            True,
            self.day_count.to_ql(),
        )
        return helper
