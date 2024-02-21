# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Interest Rate Swap instruments to be used for calibration
"""
from typing import Any, Optional, List
import pydantic
import QuantLib as ql
from aqumenlib import (
    RiskType,
    AssetClass,
    BusinessDayAdjustment,
    Frequency,
    RateIndex,
    MarketView,
)
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.index import Index
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.instruments.rate_family import RateInstrumentFamily
from aqumenlib.term import Term


class IRSwapFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    Interest Rate Swap instruments
    """

    name: str
    index: RateIndex
    day_count: Optional[DayCount] = None  # fixed leg DC
    frequency: Frequency = Frequency.ANNUAL  # fixed leg freq
    settlement_delay: Optional[int] = None
    fixed_roll_adjust: BusinessDayAdjustment = BusinessDayAdjustment.MODIFIEDFOLLOWING
    calendar: Optional[Calendar] = None
    end_of_month_flag: bool = False

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.index.currency, risk_type=RiskType.RATE, asset_class=AssetClass.RATE
        )
        self._fixed_leg_adjust = (
            self.fixed_roll_adjust.value if self.fixed_roll_adjust is not None else self.index.bd_convention
        )
        if self.day_count is None:
            self.day_count = self.index.day_count
        if self.settlement_delay is None:
            self.settlement_delay = self.index.days_to_settle
        if self.calendar is None:
            self.calendar = self.index.calendar

    def get_meta(self) -> InstrumentFamilyMeta:
        return self._inst_meta

    def get_name(self) -> str:
        return self.name

    def get_underlying_indices(self) -> List[Index]:
        return [self.index]

    def create_ql_instrument(
        self,
        market: "MarketView",
        quote_handle: ql.RelinkableQuoteHandle,
        term: Term,
        discounting_id: Optional[str] = None,
        target_curve: Optional["Curve"] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
        df_handle = ql.YieldTermStructureHandle()
        if discounting_id is not None:
            df_curve = market.get_discounting_curve_by_id(discounting_id)
            df_handle = ql.YieldTermStructureHandle(df_curve.get_ql_curve())
        if self.index.is_overnight():
            return ql.OISRateHelper(
                self.settlement_delay,
                term.to_ql(),
                quote_handle,
                self.index.get_ql_index(),
                df_handle,  # YieldTermStructureHandle discountingCurve={},
                False,  # bool telescopicValueDates=False,
                0,  # Natural paymentLag=0,
                self.fixed_roll_adjust.value,  #  paymentConvention=Following,
                self.frequency.value,  # paymentFrequency=Annual,
                self.calendar.to_ql(),  # paymentCalendar=Calendar(),
                # Period forwardStart=0*Days,
                # Spread const overnightSpread=0.0,
                # Pillar::Choice pillar=LastRelevantDate,
                # Date customPillarDate=Date(),
                # RateAveraging::Type averagingMethod=Compound,
                # ext::optional< bool > endOfMonth=ext::nullopt) -> OISRateHelper"""
            )
        else:
            return ql.SwapRateHelper(
                quote_handle,
                term.to_ql(),
                self.calendar.to_ql(),
                self.frequency.value,
                self._fixed_leg_adjust,
                self.day_count.to_ql(),
                self.index.get_ql_index(),
                ql.QuoteHandle(),  #  QuoteHandle spread=Handle< Quote >(),
                ql.Period(0, ql.Days),  #  Period fwdStart=0*Days,
                df_handle,  #  YieldTermStructureHandle discountingCurve={},
                self.settlement_delay,  #  Natural settlementDays=Null< Natural >(),
                ql.Pillar.LastRelevantDate,  #  Pillar::Choice pillar=LastRelevantDate,
                ql.Date(),  #  Date customPillarDate=Date(),
                self.end_of_month_flag,  #  bool endOfMonth=False,
                False,  #  ext::optional< bool > withIndexedCoupons=ext::nullopt
            )
