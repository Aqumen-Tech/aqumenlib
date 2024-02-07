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
    Frequency,
    RateIndex,
    MarketView,
    market_util,
)
from aqumenlib.calendar import Calendar
from aqumenlib.exception import AqumenException
from aqumenlib.index import Index
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.instruments.rate_family import RateInstrumentFamily
from aqumenlib.term import Term


class CrossCurrencySwapFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    Cross Currency Swap instrument.

    Note on used conventions. Consider a currency pair EUR-USD.
    EUR is the base currency, while USD is the quote currency.
    The quote currency indicates the amount to be paid in that
    currency for one unit of base currency.
    Hence, for a cross currency swap we define a base currency
    leg and a quote currency leg. The parameters of the instrument,
    e.g. collateral currency, basis, resetting  or constant notional
    legs are defined relative to what base and quote currencies are.
    For example, in case of EUR-USD basis swaps the collateral is paid
    in quote currency (USD), the basis is given on the base currency
    leg (EUR), etc.

    For more details see:
    N. Moreni, A. Pallavicini (2015)
    FX Modelling in Collateralized Markets: foreign measures, basis curves and pricing formulae.
    """

    name: str
    index_base: RateIndex
    index_quote: RateIndex
    settlement_delay: int
    frequency: Frequency = Frequency.QUARTERLY
    roll_adjust: BusinessDayAdjustment = BusinessDayAdjustment.MODIFIEDFOLLOWING
    calendar: Optional[Calendar] = None
    end_of_month_flag: bool = False
    spread_on_base_leg: bool = True
    rebalance_notionals: bool = True
    rebalance_on_base_leg: bool = True

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.index_base.currency,
            currency2=self.index_quote.currency,
            risk_type=RiskType.RATE,
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
        base_ccy_is_collateral = self.index_quote.currency == target_curve.currency
        if discounting_id is None:
            df_ccy = self.index_base.currency if base_ccy_is_collateral else self.index_quote.currency
            discounting_id = df_ccy.name
        df_handle = ql.YieldTermStructureHandle()
        df_curve = market.get_discounting_curve(discounting_id)
        df_handle = ql.YieldTermStructureHandle(df_curve.get_ql_curve())
        ql_index_base = market_util.get_modeled_ql_rate_index(market, self.index_base)
        ql_index_quote = market_util.get_modeled_ql_rate_index(market, self.index_quote)
        if self.calendar is None:
            self.calendar = Calendar(ql_calendar_id="NullCalendar")
        if self.rebalance_notionals:
            return ql.MtMCrossCurrencyBasisSwapRateHelper(
                quote_handle,
                term.to_ql(),
                self.settlement_delay,  # Natural fixingDays,
                self.calendar.to_ql(),  # Calendar calendar,
                self.roll_adjust.to_ql(),  # BusinessDayConvention convention,
                self.end_of_month_flag,  # bool endOfMonth,
                ql_index_base,  # ext::shared_ptr< IborIndex > baseCurrencyIndex,
                ql_index_quote,  # ext::shared_ptr< IborIndex > quoteCurrencyIndex,
                df_handle,  # YieldTermStructureHandle collateralCurve,
                base_ccy_is_collateral,  # bool isFxBaseCurrencyCollateralCurrency,
                self.spread_on_base_leg,  # bool isBasisOnFxBaseCurrencyLeg
                self.rebalance_on_base_leg,  # bool isFxBaseCurrencyLegResettable
            )
        else:
            return ql.ConstNotionalCrossCurrencyBasisSwapRateHelper(
                quote_handle,
                term.to_ql(),
                self.settlement_delay,  # Natural fixingDays,
                self.calendar.to_ql(),  # Calendar calendar,
                self.roll_adjust.to_ql(),  # BusinessDayConvention convention,
                self.end_of_month_flag,  # bool endOfMonth,
                ql_index_base,  # ext::shared_ptr< IborIndex > baseCurrencyIndex,
                ql_index_quote,  # ext::shared_ptr< IborIndex > quoteCurrencyIndex,
                df_handle,  # YieldTermStructureHandle collateralCurve,
                base_ccy_is_collateral,  # bool isFxBaseCurrencyCollateralCurrency,
                self.spread_on_base_leg,  # bool isBasisOnFxBaseCurrencyLeg
            )
