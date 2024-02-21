# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Interest Rate Basis Swap instruments to be used for calibration
"""
from typing import Any, Optional, List
import pydantic
import QuantLib as ql
from aqumenlib import (
    RiskType,
    AssetClass,
    BusinessDayAdjustment,
    Frequency,
)
from aqumenlib.calendar import Calendar
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.index import Index, RateIndex
from aqumenlib.instruments.rate_family import RateInstrumentFamily
from aqumenlib.market import MarketView
from aqumenlib import market_util
from aqumenlib.term import Term


class IRBasisSwapFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    Interest Rate Basis Swap instruments.
    Can construct basis swaps with either IBOR or OIS legs.
    """

    name: str
    index1: RateIndex
    index2: RateIndex
    settlement_delay: Optional[int] = None
    frequency1: Optional[Frequency] = None
    frequency2: Optional[Frequency] = None
    payment_adjust: BusinessDayAdjustment = BusinessDayAdjustment.MODIFIEDFOLLOWING
    calendar: Optional[Calendar] = None
    end_of_month_flag: bool = False

    def model_post_init(self, __context: Any) -> None:
        if self.index1.currency != self.index2.currency:
            raise RuntimeError("IR basis swap cannot be constructed with indices from different currencies.")
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.index1.currency, risk_type=RiskType.RATEBASIS, asset_class=AssetClass.RATE
        )
        self._init_leg_frequency()
        if self.settlement_delay is None:
            self.settlement_delay = max(self.index1.days_to_settle, self.index2.days_to_settle)
        if self.calendar is None:
            self.calendar = self.index1.calendar

    def get_meta(self) -> InstrumentFamilyMeta:
        return self._inst_meta

    def get_name(self) -> str:
        return self.name

    def get_underlying_indices(self) -> List[Index]:
        return [self.index1, self.index2]

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
        if self.index1.is_overnight() and self.index2.is_overnight():
            raise NotImplementedError("Overnight-Overnight basis instrument is not implemented yet")

        df_handle = ql.YieldTermStructureHandle()
        if discounting_id is not None:
            df_curve = market.get_discounting_curve_by_id(discounting_id)
            df_handle = ql.YieldTermStructureHandle(df_curve.get_ql_curve())
        if target_curve is None or target_curve.target_index is None:
            raise RuntimeError("Basis instrument used without target index being known.")

        if not self.index1.is_overnight() and not self.index2.is_overnight():
            build_index1 = target_curve.target_index == self.index1
            if build_index1:
                ql_index1 = self.index1.get_ql_index()
                ql_index2 = market_util.get_modeled_ql_rate_index(market, self.index2)
            else:
                ql_index2 = self.index2.get_ql_index()
                ql_index1 = market_util.get_modeled_ql_rate_index(market, self.index1)
            return ql.IborIborBasisSwapRateHelper(
                quote_handle,  # QuoteHandle basis,
                term.to_ql(),  # Period tenor,
                self.settlement_delay,  # Natural settlementDays,
                self.calendar.to_ql(),  # Calendar calendar,
                self.payment_adjust.value,  # BusinessDayConvention convention,
                self.end_of_month_flag,  # bool endOfMonth,
                ql_index1,  # ext::shared_ptr< IborIndex > const & baseIndex,
                ql_index2,  # ext::shared_ptr< IborIndex > const & otherIndex,
                df_handle,  # YieldTermStructureHandle discountHandle,
                build_index1,  # bool bootstrapBaseCurve)
            )
        else:
            on_index = self.index1 if self.index1.is_overnight() else self.index2
            ib_index = self.index2 if self.index1.is_overnight() else self.index1
            if on_index.get_name() == target_curve.target_index:
                raise NotImplementedError(
                    "Overnight-IBOR basis instrument does not yet support calibration of O/N side."
                )
            else:
                ql_on_index = market_util.get_modeled_ql_rate_index(market, on_index)
            ql_ib_index = ib_index.get_ql_index()
            return ql.OvernightIborBasisSwapRateHelper(
                quote_handle,  # QuoteHandle basis,
                term.to_ql(),  # Period tenor,
                self.settlement_delay,  # Natural settlementDays,
                self.calendar.to_ql(),  # Calendar calendar,
                self.payment_adjust.value,  # BusinessDayConvention convention,
                self.end_of_month_flag,  # bool endOfMonth,
                ql_on_index,  # ext::shared_ptr< OvernightIndex > const & baseIndex,
                ql_ib_index,  # ext::shared_ptr< IborIndex > const & otherIndex,
                df_handle,  # YieldTermStructureHandle discountHandle=Handle< YieldTermStructure >()
            )

    def _init_leg_frequency(self):
        self.frequency1 = _guess_leg_frequency(self.frequency1, self.index1, self.index2)
        self.frequency2 = _guess_leg_frequency(self.frequency2, self.index2, self.index1)


def _guess_leg_frequency(freq: Frequency, rate_index: RateIndex, other_index: RateIndex) -> Frequency:
    if freq is not None:
        return freq
    if not rate_index.is_overnight():
        return Frequency(rate_index.tenor.to_ql().frequency())
    if not other_index.is_overnight():
        return Frequency(other_index.tenor.to_ql().frequency())
    return Frequency.ANNUAL
