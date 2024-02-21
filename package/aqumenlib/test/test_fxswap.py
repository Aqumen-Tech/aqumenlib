# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
test FX swaps
"""

from aqumenlib.enums import Metric
from aqumenlib.instrument import create_instrument
from aqumenlib.instruments.fxswap_family import FXSwapFamily
from aqumenlib.instruments.xccy_family import CrossCurrencySwapFamily
from aqumenlib.pricer import set_global_reporting_currency
from aqumenlib.pricers.fxswap_pricer import FXSwapPricer
from aqumenlib.test.test_xccy_csa import make_euraud_domestic_model, make_eurxaud_xccy_model
from aqumenlib.trade import TradeInfo
import pytest

from aqumenlib import (
    Date,
    Currency,
    MarketView,
    RateInterpolationType,
)
from aqumenlib.calendar import Calendar, date_advance
from aqumenlib import indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
    add_bootstraped_rate_curve_to_market,
    add_bootstraped_xccy_discounting_curve_to_market,
)

from aqumenlib.cashflow import Cashflow, Cashflows
from aqumenlib.products.fxswap import FXSwap


def test_fxswap_pricing():
    """
    Basis tests for FX swap
    """
    pricing_date = Date.from_any("2023-11-27")
    tcase = [0.05, 0.05, 0.03, 0.05, 0.01, False, True]
    market = make_euraud_domestic_model(
        pricing_date=pricing_date,
        dom_fwd=0.05,
        dom_dsc=0.05,
        frn_fwd=0.07,
        frn_dsc=0.07,
    )

    market.add_spot_FX(Currency.EUR, Currency.AUD, 1.7)
    fxfam = FXSwapFamily(
        name="EURAUD FX swap",
        currency_base=Currency.EUR,
        currency_quote=Currency.AUD,
        settlement_delay=2,
        calendar=Calendar(ql_calendar_id="TARGET"),
    )
    curve_aud_x = add_bootstraped_xccy_discounting_curve_to_market(
        name="AUD XCCY Curve",
        market=market,
        instruments=[
            create_instrument((fxfam, "6M"), 0.0043),
            create_instrument((fxfam, "1Y"), 0.0150),
        ],
        target_currency=Currency.AUD,
        csa_id="AUDxEUR",
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    set_global_reporting_currency(Currency.EUR)

    fxswap = FXSwap(
        name="test FX swap",
        base_currency=Currency.EUR,
        quote_currency=Currency.AUD,
        start_date=Date.from_any("2023-11-29"),
        maturity_date=Date.from_any("2024-11-29"),
        base_fx=1.7,
        forward_points=0.0150,
    )
    fxswap_pricer = FXSwapPricer(
        fxswap=fxswap, market=market, trade_info=TradeInfo(trade_id="test pricer", amount=1_000_000, is_receive=False)
    )
    print(fxswap_pricer.get_cashflows())
    print("Value:", fxswap_pricer.value())
    print("Reporting currency value:", fxswap_pricer.calculate(Metric.REPORTING_MARKET_VALUE))


test_fxswap_pricing()
