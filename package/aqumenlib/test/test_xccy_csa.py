# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
test pricing with cross-currency CSA (Credit Support Annex)
"""

from aqumenlib.instrument import create_instrument
from aqumenlib.instruments.xccy_family import CrossCurrencySwapFamily
import pytest

from aqumenlib import (
    Date,
    Currency,
    Frequency,
    MarketView,
    Instrument,
    BusinessDayAdjustment,
    Metric,
    RateInterpolationType,
    set_global_reporting_currency,
    TradeInfo,
)
from aqumenlib.cashflow import Cashflow
from aqumenlib.daycount import DayCount
from aqumenlib.calendar import Calendar
from aqumenlib.pricers.irs_pricer import InterestRateSwapPricer
from aqumenlib.products.irs import InterestRateSwap
from aqumenlib.risk import calculate_market_risk
from aqumenlib import indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
    add_bootstraped_rate_curve_to_market,
    add_bootstraped_xccy_discounting_curve_to_market,
)


def test_eurxaud_csa_model():
    """
    Test the use case where funds for trading in AUD are raised
    in FX market by using EUR collateral.

    In this situation, EUR DF curve can be built from domestic EUR
    instruments, while discounting curve for AUD should be bootstrapped from
    FX instruments such as FX or cross-currency swaps.

    """
    pricing_date = Date.from_any("2023-11-28")
    market = MarketView(name="test model", pricing_date=pricing_date)
    curve_estr = add_bootstraped_discounting_rate_curve_to_market(
        name="ESTR Curve",
        market=market,
        instruments=[
            create_instrument("IRS-ESTR-1Y", 0.04),
            create_instrument("IRS-ESTR-10Y", 0.04),
            create_instrument("IRS-ESTR-30Y", 0.04),
        ],
        rate_index=indices.ESTR,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_euribor3m = add_bootstraped_rate_curve_to_market(
        name="EURIBOR3M Curve",
        market=market,
        instruments=[
            create_instrument("IRS-EURIBOR3M-1Y", 0.05),
            create_instrument("IRS-EURIBOR3M-10Y", 0.05),
            create_instrument("IRS-EURIBOR3M-30Y", 0.05),
        ],
        rate_index=indices.EURIBOR3M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_aonia = add_bootstraped_discounting_rate_curve_to_market(
        name="AONIA Curve",
        market=market,
        instruments=[
            create_instrument("IRS-AONIA-1Y", 0.05),
            create_instrument("IRS-AONIA-10Y", 0.05),
            create_instrument("IRS-AONIA-30Y", 0.05),
        ],
        rate_index=indices.AONIA,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_bbsw3m = add_bootstraped_rate_curve_to_market(
        name="BBSW3M Curve",
        market=market,
        instruments=[
            create_instrument("IRS-BBSW3M-1Y", 0.06),
            create_instrument("IRS-BBSW3M-10Y", 0.06),
            create_instrument("IRS-BBSW3M-30Y", 0.06),
        ],
        rate_index=indices.BBSW3M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    xfam = CrossCurrencySwapFamily(
        name="EURAUD XCCY swap",
        index_base=indices.EURIBOR3M,
        index_quote=indices.BBSW3M,
        settlement_delay=2,
        calendar=Calendar(ql_calendar_id="TARGET"),
    )
    curve_aud_x = add_bootstraped_xccy_discounting_curve_to_market(
        name="BBSW3M XCCY Curve",
        market=market,
        instruments=[
            create_instrument((xfam, "1Y"), 0.01),
            create_instrument((xfam, "10Y"), 0.01),
            create_instrument((xfam, "30Y"), 0.01),
        ],
        target_currency=Currency.AUD,
        target_discounting_id="AUDxEUR",
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    for c in [
        curve_estr,
        curve_euribor3m,
        curve_aonia,
        curve_bbsw3m,
        curve_aud_x,
    ]:
        print(f"{c.get_name()}  {c.zero_rate(Date.from_isoint(20241128))}")
    assert curve_aud_x.zero_rate(Date.from_isoint(20241128)) == pytest.approx(0.04, abs=0.002)


# test_eurxaud_csa_model()
