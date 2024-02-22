# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Inflation instruments to be used for calibration
"""

from typing import Any, Optional, List
import pydantic
import QuantLib as ql
from aqumenlib import (
    RiskType,
    AssetClass,
    BusinessDayAdjustment,
    MarketView,
)
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.instrument_family import InstrumentFamily
from aqumenlib.term import Term
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.index import Index, InflationIndex
from aqumenlib import market_util


class InflationZeroCouponSwapFamily(InstrumentFamily, pydantic.BaseModel):
    """
    Zero Coupon Inflation Swap instrument family
    """

    name: str
    index: InflationIndex
    day_count: DayCount
    observation_lag: Term
    payment_adjust: BusinessDayAdjustment = BusinessDayAdjustment.FOLLOWING
    calendar: Optional[Calendar] = None

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.index.currency, risk_type=RiskType.INFLATION, asset_class=AssetClass.INFLATION
        )
        if self.calendar is None:
            self.calendar = Calendar(ql_calendar_id="NullCalendar")

    def get_meta(self) -> InstrumentFamilyMeta:
        return self._inst_meta

    def get_name(self) -> str:
        return self.name

    def get_underlying_indices(self) -> List[Index]:
        return [self.index]

    def create_ql_instrument(
        self,
        market: MarketView,
        quote_handle: ql.RelinkableQuoteHandle,
        term: Term,
        discounting_id: Optional[str] = None,
        target_curve: Optional["Curve"] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
        ccy = self.index.currency
        df = market.get_discounting_curve(ccy)
        df_handle = ql.RelinkableYieldTermStructureHandle()
        df_handle.linkTo(df.get_ql_curve())
        ql_index = self.index.ql_index.clone(ql.ZeroInflationTermStructureHandle())
        market_util.add_fixings_to_ql_index(market, self.index.get_name(), ql_index)
        return ql.ZeroCouponInflationSwapHelper(
            quote_handle,  # QuoteHandle quote,
            self.observation_lag.to_ql(),  # Period lag,
            market.pricing_date.to_ql() + term.to_ql(),  # Date maturity,
            self.calendar.to_ql(),  # Calendar calendar,
            self.payment_adjust.value,  # BusinessDayConvention bcd,
            self.day_count.to_ql(),  # DayCounter dayCounter,
            ql_index,  # ext::shared_ptr< ZeroInflationIndex > const & index,
            ql.CPI.AsIndex,  # CPI::InterpolationType observationInterpolation,
            df_handle,  # YieldTermStructureHandle nominalTS
        )
