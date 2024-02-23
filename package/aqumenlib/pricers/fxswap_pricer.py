# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
FX Swap, FX Forward and FX NDF (non-deliverable forward) pricers
"""
from typing import Any, Dict
import pydantic

from aqumenlib import (
    Date,
    Currency,
    MarketView,
    Pricer,
    Metric,
    TradeInfo,
)

from aqumenlib.cashflow import Cashflow, Cashflows
from aqumenlib.products.fxswap import FXSwap


class FXSwapPricer(Pricer, pydantic.BaseModel):
    """
    Pricer for FX Swap, FX Forward and FX NDF (non-deliverable forward).
    See product class FXSwap for conventions.
    """

    fxswap: FXSwap
    market: MarketView
    trade_info: TradeInfo = TradeInfo()

    def model_post_init(self, __context: Any) -> None:
        self.set_market(self.market)
        self._pay_rec = 1.0 if self.trade_info.is_receive else -1.0

    def get_market(self) -> "MarketView":
        return self.market

    def set_market(self, market_model: MarketView):
        self.market: MarketView = market_model
        self.market.ql_set_pricing_date()

    def get_name(self) -> str:
        if self.trade_info.trade_id:
            return self.trade_info.trade_id
        else:
            return self.fxswap.name

    def value(self) -> Dict[Currency, float]:
        """
        Valuation in each currency of the cash flows.
        """
        result = {
            self.fxswap.base_currency: 0.0,
            self.fxswap.quote_currency: 0.0,
        }
        cashflows = self.get_cashflows(include_past=False)
        for cf in cashflows.flows:
            df_curve = self.market.get_discounting_curve(cf.currency, self.trade_info.csa_id)
            v = cf.amount * df_curve.discount_factor(cf.date)
            result[cf.currency] += v
        return result

    def value_in_ccy(self, currency: Currency) -> float:
        """
        Return value converted to a given currency.
        """
        v_dict = self.value()
        total = 0.0
        for c, v in v_dict.items():
            fx = self.market.get_spot_FX(currency, c)
            total += v / fx
        return total

    def get_cashflows(self, include_past: bool = False) -> Cashflows:
        """
        Return FX swap cash flows.
        """
        # TODO handle NDF
        dt = self.market.pricing_date.to_ql()
        flows = []
        if self.fxswap.initial_exchange and (include_past or self.fxswap.start_date.to_ql() >= dt):
            flow = Cashflow(
                currency=self.fxswap.base_currency,
                date=self.fxswap.start_date,
                amount=self.trade_info.amount * self._pay_rec,
                notional=self.trade_info.amount,
            )
            flows.append(flow)
            flow = Cashflow(
                currency=self.fxswap.quote_currency,
                date=self.fxswap.start_date,
                amount=-1 * self.trade_info.amount * self._pay_rec * self.fxswap.base_fx,
                notional=self.trade_info.amount,
            )
            flows.append(flow)
        if include_past or self.fxswap.maturity_date.to_ql() >= dt:
            flow = Cashflow(
                currency=self.fxswap.base_currency,
                date=self.fxswap.maturity_date,
                amount=-1 * self.trade_info.amount * self._pay_rec,
                notional=self.trade_info.amount,
            )
            flows.append(flow)
            flow = Cashflow(
                currency=self.fxswap.quote_currency,
                date=self.fxswap.maturity_date,
                amount=self.trade_info.amount * self._pay_rec * (self.fxswap.base_fx + self.fxswap.forward_points),
                notional=self.trade_info.amount,
            )
            flows.append(flow)
        return Cashflows(flows=flows)

    def calculate(self, metric: Metric) -> Any:
        self.market.ql_set_pricing_date()
        match metric:
            case Metric.NATIVE_MARKET_VALUE | Metric.NATIVE_MODEL_VALUE:
                return self.value()
            case Metric.VALUE | Metric.MARKET_VALUE | Metric.MODEL_VALUE | Metric.RISK_VALUE:
                return self.value()
            case Metric.REPORTING_VALUE | Metric.REPORTING_MARKET_VALUE | Metric.REPORTING_MODEL_VALUE:
                return self.value_in_ccy(self.get_pricer_settings().reporting_currency)
            case Metric.CURRENCY:
                return self.fxswap.base_currency
            case Metric.CURRENCY_OTHER:
                return self.fxswap.quote_currency
            case Metric.CASHFLOWS:
                return self.get_cashflows()
            case _:
                return "N/A"
