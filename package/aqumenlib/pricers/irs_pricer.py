# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Pricers interest rate swaps - IBOR and OIS.
"""
from typing import Any
import pydantic
import QuantLib as ql

from aqumenlib import (
    Date,
    MarketView,
    Pricer,
    Metric,
    TradeInfo,
)
from aqumenlib import market_util
from aqumenlib.cashflow import Cashflow, Cashflows
from aqumenlib.products.irs import InterestRateSwap


class InterestRateSwapPricer(Pricer, pydantic.BaseModel):
    """
    Pricer for vanilla interest rate swaps - IBOR and OIS.
    This pricer is to be used when there are no special features on the swaps
    like amortization, compounding, etc.
    """

    swap: InterestRateSwap
    market: MarketView
    trade_info: TradeInfo = TradeInfo()

    def model_post_init(self, __context: Any) -> None:
        self.set_market(self.market)

    def get_market(self) -> "MarketView":
        return self.market

    def set_market(self, market_model: MarketView):
        self.market: MarketView = market_model
        self.market.ql_set_pricing_date()
        _discount_curve = self.market.get_discounting_curve(self.swap.index.currency)
        df_ts = ql.RelinkableYieldTermStructureHandle()
        df_ts.linkTo(_discount_curve.get_ql_curve())
        engine = ql.DiscountingSwapEngine(df_ts)
        ql_index = market_util.get_modeled_ql_rate_index(self.market, self.swap.index)
        pay_rec = ql.Swap.Receiver if self.trade_info.is_receive else ql.Swap.Payer
        if self.swap.index.is_overnight():
            self._ql_swap = ql.OvernightIndexedSwap(
                pay_rec,  # Swap::Type type,
                self.trade_info.amount,  # Real nominal,
                self.swap.get_ql_schedule_fixed(),  # Schedule schedule,
                self.swap.fixed_coupon,  # Rate fixedRate,
                self.swap.fixed_day_count.to_ql(),  # DayCounter fixedDC,
                ql_index,  # ext::shared_ptr< OvernightIndex > const & index,
                self.swap.float_spread,  # Spread spread=0.0,
                self.swap.payment_lag,  # Natural paymentLag=0,
                self.swap.payment_adjust.value,  # BusinessDayConvention paymentAdjustment=Following,
                self.swap.payment_calendar.to_ql(),  # Calendar paymentCalendar=Calendar(),
                False,  # bool telescopicValueDates=False,
                ql.RateAveraging.Compound,  # RateAveraging::Type averagingMethod=Compound)
            )
        else:
            self._ql_swap = ql.VanillaSwap(
                pay_rec,  # Swap::Type type,
                self.trade_info.amount,  # Real nominal,
                self.swap.get_ql_schedule_fixed(),  # Schedule fixedSchedule,
                self.swap.fixed_coupon,  # Rate fixedRate,
                self.swap.fixed_day_count.to_ql(),  # DayCounter fixedDayCount,
                self.swap.get_ql_schedule_floating(),  # Schedule floatSchedule,
                ql_index,  # ext::shared_ptr< IborIndex > const & index,
                self.swap.float_spread,  # Spread spread,
                self.swap.index.day_count.to_ql(),  # DayCounter floatingDayCount,
                # ext::optional< bool > withIndexedCoupons=ext::nullopt) -> VanillaSwap"""
            )
        self._ql_swap.setPricingEngine(engine)

    def get_name(self):
        if self.trade_info.trade_id:
            return self.trade_info.trade_id
        else:
            return self.swap.name

    def value(self):
        """
        Valuation in native currency
        """
        return self._ql_swap.NPV()

    def par_coupon(self):
        """
        Par fixed leg coupon
        """
        return self._ql_swap.fairRate()

    def par_spread(self):
        """
        Par floating spread
        """
        return self._ql_swap.fairSpread()

    def calculate(self, metric: Metric) -> Any:
        self.market.ql_set_pricing_date()
        match metric:
            case Metric.NATIVE_MARKET_VALUE | Metric.NATIVE_MODEL_VALUE:
                return self.value()
            case Metric.VALUE | Metric.MARKET_VALUE | Metric.MODEL_VALUE | Metric.RISK_VALUE:
                return [(self.swap.index.currency, self.value())]
            case Metric.REPORTING_VALUE | Metric.REPORTING_MARKET_VALUE | Metric.REPORTING_MODEL_VALUE:
                fx = self.market.get_spot_FX(
                    self.get_pricer_settings().reporting_currency,
                    self.swap.index.currency,
                )
                return self.value() / fx
            case Metric.CURRENCY:
                return self.swap.index.currency
            case Metric.CASHFLOWS:
                dt = self.market.pricing_date.to_ql()
                flows = []
                for ileg, leg in enumerate([self._ql_swap.leg(0), self._ql_swap.leg(1)]):
                    sign = -1 if ileg == 0 else 1
                    if self.trade_info.is_receive:
                        sign *= -1
                    for _, cf in enumerate(leg):
                        if cf.date() >= dt:
                            flow = Cashflow(
                                currency=self.swap.index.currency,
                                date=Date.from_ql(cf.date()),
                                amount=cf.amount() * sign,
                                notional=self.trade_info.amount,
                            )
                            flow.add_meta_from_ql(cf)
                            flows.append(flow)
                return Cashflows(flows=flows)
            case _:
                return "N/A"
