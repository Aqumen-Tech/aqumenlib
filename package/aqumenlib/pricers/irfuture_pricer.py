# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Interest Rate Futures pricer
"""
from typing import Any, Dict, Optional
import pydantic
from aqumenlib.instrument_type import InstrumentType
from aqumenlib.instruments.future_contract import futures_symbol_to_month_start
from aqumenlib.market_util import get_modeled_ql_rate_index

from aqumenlib import (
    Currency,
    MarketView,
    Pricer,
    Metric,
    TradeInfo,
)
import QuantLib as ql


class IRFuturePricer(Pricer, pydantic.BaseModel):
    """
    Pricer for Interest Rate Futures.
    As an underlying product, InstrumentType build from IRFutureFamily class should be used.
    """

    contract: InstrumentType
    market: MarketView
    trade_info: TradeInfo = TradeInfo()
    last_settlement_price: Optional[float] = None
    market_price: Optional[float] = None

    def model_post_init(self, __context: Any) -> None:
        self._pay_rec = 1.0 if self.trade_info.is_receive else -1.0
        self.set_market(self.market)

    def get_market(self) -> "MarketView":
        return self.market

    def set_market(self, market_model: MarketView):
        self.market: MarketView = market_model
        self.market.ql_set_pricing_date()
        contract_type = self.contract.family.get_contract_type()
        ql_index = get_modeled_ql_rate_index(self.market, contract_type.get_index())
        series = futures_symbol_to_month_start(self.contract.specifics)
        self._ql_future = ql.OvernightIndexFuture(
            ql_index,  #  ext::shared_ptr< OvernightIndex > overnightIndex,
            contract_type.accrual_start_date(series).to_ql(),  # Date valueDate,
            contract_type.accrual_end_date(series).to_ql(),  # Date maturityDate,
            ql.QuoteHandle(),  # QuoteHandle convexityAdjustment=Handle< Quote >(),
            contract_type.rate_averaging().to_ql(),  # RateAveraging::Type averagingMethod=Compound
        )

    def get_name(self) -> str:
        if self.trade_info.trade_id:
            return self.trade_info.trade_id
        else:
            return self.contract.name

    def model_value(self) -> Dict[Currency, float]:
        """
        Valuation in each currency of the cash flows.
        """
        fut_ccy = self.contract.family.get_meta().currency
        return {fut_ccy: self._ql_future.NPV() * self._pay_rec}

    def market_value(self) -> Dict[Currency, float]:
        """
        Valuation in each currency of the cash flows.
        """
        fut_ccy = self.contract.family.get_meta().currency
        if self.market_price is None:
            return "N/A"
        else:
            return {fut_ccy: self.market_price * self._pay_rec}

    def calculate(self, metric: Metric) -> Any:
        self.market.ql_set_pricing_date()
        match metric:
            case Metric.NATIVE_MARKET_VALUE | Metric.NATIVE_MODEL_VALUE:
                return self.market_value()
            case Metric.VALUE | Metric.MARKET_VALUE | Metric.MODEL_VALUE | Metric.RISK_VALUE:
                return self.model_value()
            case Metric.REPORTING_VALUE | Metric.REPORTING_MARKET_VALUE | Metric.REPORTING_MODEL_VALUE:
                ccy = self.get_pricer_settings().reporting_currency
                fut_ccy = self.contract.family.get_meta().currency
                fx = self.market.get_spot_FX(fut_ccy, ccy)
                v = self.model_value()
                return v / fx
            case Metric.CURRENCY:
                return self.contract.family.get_meta().currency
            case _:
                return "N/A"
