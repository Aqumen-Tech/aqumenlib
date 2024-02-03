# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from typing import Any, Optional, List
import pydantic
import QuantLib as ql

from aqumenlib import (
    Currency,
    RiskType,
    AssetClass,
    BusinessDayAdjustment,
    Frequency,
)
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.index import Index
from aqumenlib.instruments.rate_family import RateInstrumentFamily
from aqumenlib.market import MarketView
from aqumenlib.term import Term


class ZeroCouponBondFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    Zero coupon cash instrument - can represent T-Bills and similar instruments.
    Can also be used to build curves out of zero rates (this is also the default configuration of this class).
    Quotes are assumed to be provided as yield.
    """

    name: str
    currency: Currency
    settlement_delay: int
    payment_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    yield_day_count: Optional[DayCount] = None
    compound_frequency: Frequency = Frequency.ANNUAL
    calendar: Optional[Calendar] = None

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.currency, risk_type=RiskType.RATE, asset_class=AssetClass.RATE
        )
        if self.calendar is None:
            self.calendar = Calendar(ql_calendar_id="NullCalendar")
        if self.yield_day_count is None:
            self.yield_day_count = DayCount.ACT365F

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
        value_date = market.pricing_date.to_ql()
        zc_bond = ql.ZeroCouponBond(
            self.settlement_delay,
            self.calendar.to_ql(),
            100,
            value_date + term.to_ql(),
            self.payment_adjust.value,
            100.0,
            value_date,
        )
        zc_bond.setPricingEngine(
            ql.DiscountingBondEngine(
                ql.YieldTermStructureHandle(ql.FlatForward(value_date, quote_handle, ql.Actual365Fixed()))
            )
        )
        clean_price = zc_bond.cleanPrice(
            quote_handle.value(), self.yield_day_count.to_ql(), ql.Compounded, self.compound_frequency.value
        )
        return ql.BondHelper(ql.QuoteHandle(ql.SimpleQuote(clean_price)), zc_bond)
