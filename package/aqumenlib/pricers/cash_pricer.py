# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
CashFlowPricer class
"""
from typing import Any, List
import pydantic
import QuantLib as ql

from aqumenlib import MarketView, Pricer, Metric
from aqumenlib.cashflow import Cashflow, Cashflows


class CashFlowPricer(Pricer, pydantic.BaseModel):
    """
    Pricer for computing analyitcs metrics on a set of fixed cash flows.
    Assumes single currency for all flows.
    """

    name: str
    market: MarketView
    market_price: float
    flows: List[Cashflow]

    def model_post_init(self, __context: Any) -> None:
        if not self.flows:
            raise NotImplementedError("Cannot construct cash flow pricer with no cash flows")
        self._currency = self.flows[0].currency
        self._ql_leg = ql.Leg()
        for f in self.flows:
            self._ql_leg.append(ql.SimpleCashFlow(f.amount, f.date.to_ql()))
        self.set_market(self.market)

    def get_market(self) -> "MarketView":
        return self.market

    def set_market(self, market_model: MarketView):
        self.market: MarketView = market_model
        self.market.ql_set_pricing_date()
        self._cache_discount_curve = self.market.get_discounting_curve(self._currency)
        self._cache_df_ql_handle = ql.YieldTermStructureHandle(self._cache_discount_curve.get_ql_curve())
        self._cache_model_value = ql.CashFlows.npv(self._ql_leg, self._cache_df_ql_handle, False)
        irr_price = self.market_price
        if abs(irr_price) == 0.0:
            irr_price = self._cache_model_value
        self._cache_irr = ql.CashFlows.yieldRate(
            self._ql_leg,
            irr_price,
            ql.Actual365Fixed(),
            ql.Compounded,
            ql.Annual,
            True,
        )

    def get_name(self):
        return self.name

    def rebucket_to_model_times(self, time_points=List[float], convert_to_reporting_ccy=False) -> List[float]:
        """
        Given a list of absolute times treat it as bucket or histogram boundaries
        and return a list of same size of associated accumulated cashflows
        """
        anchor = self.market.pricing_date.to_excel()
        reporting_ccy = self.get_pricer_settings().reporting_currency
        result = [0.0] * len(time_points)
        for iflow in self.flows:
            t = (iflow.date.to_excel() - anchor) / 365.0
            for i, ipoint in enumerate(time_points):
                if t > ipoint:
                    continue
                else:
                    fx = 1.0
                    if convert_to_reporting_ccy:
                        fx = self.market.get_fwd_FX(iflow.date, reporting_ccy, self._currency)
                    result[i] += iflow.amount / fx
                    break
        return result

    def calculate(self, metric: Metric) -> Any:
        self.market.ql_set_pricing_date()
        match metric:
            case Metric.NATIVE_MARKET_VALUE:
                return self.market_price
            case Metric.NATIVE_MODEL_VALUE:
                return self._cache_model_value
            case Metric.VALUE | Metric.MARKET_VALUE:
                return [(self._currency, self.market_price)]
            case Metric.MODEL_VALUE | Metric.RISK_VALUE:
                return [(self._currency, self._cache_model_value)]
            case Metric.REPORTING_VALUE | Metric.REPORTING_MARKET_VALUE:
                fx = self.market.get_spot_FX(
                    self.get_pricer_settings().reporting_currency,
                    self._currency,
                )
                return self.market_price / fx
            case Metric.REPORTING_MODEL_VALUE:
                fx = self.market.get_spot_FX(
                    self.get_pricer_settings().reporting_currency,
                    self._currency,
                )
                return self._cache_model_value / fx
            case Metric.IRR:
                return self._cache_irr
            case Metric.DURATION | Metric.DURATION_MACAULAY:
                dur_type = ql.Duration.Modified
                if metric == Metric.DURATION_MACAULAY:
                    dur_type = ql.Duration.Macaulay
                rate = ql.InterestRate(
                    self._cache_irr,
                    ql.Actual365Fixed(),
                    ql.Compounded,
                    ql.Annual,
                )
                return ql.CashFlows.duration(self._ql_leg, rate, dur_type, False)
            case Metric.CONVEXITY:
                rate = ql.InterestRate(
                    self._cache_irr,
                    ql.Actual365Fixed(),
                    ql.Compounded,
                    ql.Annual,
                )
                return ql.CashFlows.convexity(self._ql_leg, rate, False)
            case Metric.ZSPREAD:
                irr_price = self.market_price
                if abs(irr_price) == 0.0:
                    irr_price = self._cache_model_value
                return ql.CashFlows.zSpread(
                    self._ql_leg,
                    irr_price,
                    self._cache_discount_curve.get_ql_curve(),
                    ql.Actual365Fixed(),
                    ql.Compounded,
                    ql.Annual,
                    True,
                )
            case Metric.CURRENCY:
                return self._currency
            case Metric.CASHFLOWS:
                return Cashflows(flows=self.flows)
            case _:
                return "N/A"
