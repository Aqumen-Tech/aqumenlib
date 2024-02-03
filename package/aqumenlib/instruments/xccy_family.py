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
    frequency: Frequency = Frequency.QUARTERLY
    settlement_delay: int
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
        target_index: Optional[Index] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
        if discounting_id is None:
            raise AqumenException("Discounting curve ID must be provided for collateral currency")
        df_handle = ql.YieldTermStructureHandle()
        df_curve = market.get_discounting_curve(discounting_id)
        df_handle = ql.YieldTermStructureHandle(df_curve.get_ql_curve())
        base_ccy_is_collateral = self.index_base.currency == df_curve.currency
        if self.rebalance_notionals:
            return ql.ConstNotionalCrossCurrencyBasisSwapRateHelper(
                quote_handle,
                term.to_ql(),
                self.settlement_delay,  # Natural fixingDays,
                self.calendar.to_ql(),  # Calendar calendar,
                self.roll_adjust.to_ql(),  # BusinessDayConvention convention,
                self.end_of_month_flag,  # bool endOfMonth,
                self.index_base.get_ql_index(),  # ext::shared_ptr< IborIndex > baseCurrencyIndex,
                self.index_quote.get_ql_index(),  # ext::shared_ptr< IborIndex > quoteCurrencyIndex,
                df_handle,  # YieldTermStructureHandle collateralCurve,
                base_ccy_is_collateral,  # bool isFxBaseCurrencyCollateralCurrency,
                self.spread_on_base_leg,  # bool isBasisOnFxBaseCurrencyLeg
            )
        else:
            return ql.MtMCrossCurrencyBasisSwapRateHelper(
                quote_handle,
                term.to_ql(),
                self.settlement_delay,  # Natural fixingDays,
                self.calendar.to_ql(),  # Calendar calendar,
                self.roll_adjust.to_ql(),  # BusinessDayConvention convention,
                self.end_of_month_flag,  # bool endOfMonth,
                self.index_base.get_ql_index(),  # ext::shared_ptr< IborIndex > baseCurrencyIndex,
                self.index_quote.get_ql_index(),  # ext::shared_ptr< IborIndex > quoteCurrencyIndex,
                df_handle,  # YieldTermStructureHandle collateralCurve,
                base_ccy_is_collateral,  # bool isFxBaseCurrencyCollateralCurrency,
                self.spread_on_base_leg,  # bool isBasisOnFxBaseCurrencyLeg
                self.rebalance_on_base_leg,  # bool isFxBaseCurrencyLegResettable
            )
