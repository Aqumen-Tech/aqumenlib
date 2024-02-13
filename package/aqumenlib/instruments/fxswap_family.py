# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Cross Currency Swap instruments to be used for calibration
"""
from typing import Any, Optional, List
import pydantic
import QuantLib as ql
from aqumenlib import (
    RiskType,
    AssetClass,
    BusinessDayAdjustment,
    Currency,
    MarketView,
)
from aqumenlib.calendar import Calendar
from aqumenlib.index import Index
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.instruments.rate_family import RateInstrumentFamily
from aqumenlib.term import Term


class FXSwapFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    FX Swap instrument.
    """

    name: str
    currency_base: Currency
    currency_quote: Currency
    settlement_delay: int
    roll_adjust: BusinessDayAdjustment = BusinessDayAdjustment.MODIFIEDFOLLOWING
    end_of_month_flag: bool = False
    calendar: Optional[Calendar] = None
    trading_calendar: Optional[Calendar] = None

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.currency_base,
            currency2=self.currency_quote,
            risk_type=RiskType.FX,
            asset_class=AssetClass.FX,
        )

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
        discounting_id: Optional[str],
        target_curve: Optional["Curve"] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
        base_ccy_is_collateral = self.currency_base != target_curve.currency
        if discounting_id is None:
            df_ccy = self.currency_base if base_ccy_is_collateral else self.currency_quote
            discounting_id = df_ccy.name
        df_curve = market.get_discounting_curve(discounting_id)
        df_handle = ql.YieldTermStructureHandle(df_curve.get_ql_curve())
        if self.calendar is None:
            self.calendar = Calendar(ql_calendar_id="NullCalendar")
        if self.trading_calendar is None:
            self.trading_calendar = Calendar(ql_calendar_id="NullCalendar")
        spot_fx_handle = ql.RelinkableQuoteHandle(
            ql.SimpleQuote(market.get_spot_FX(self.currency_base, self.currency_quote))
        )

        return ql.FxSwapRateHelper(
            quote_handle,  # QuoteHandle fwdPoint
            spot_fx_handle,  # QuoteHandle spotFx
            term.to_ql(),  # Period tenor
            self.settlement_delay,  # Natural fixingDay
            self.calendar.to_ql(),  # Calendar calendar
            self.roll_adjust.to_ql(),  # BusinessDayConvention convention
            self.end_of_month_flag,  # bool endOfMonth
            base_ccy_is_collateral,  # bool isFxBaseCurrencyCollateralCurrency
            df_handle,  # YieldTermStructureHandle collateralCurve
            self.trading_calendar.to_ql(),  # Calendar tradingCalendar=Calendar()
        )
