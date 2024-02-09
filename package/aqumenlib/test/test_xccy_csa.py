# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
test pricing with cross-currency CSA (Credit Support Annex)
"""

from aqumenlib.instrument import create_instrument
from aqumenlib.instruments.fxswap_family import FXSwapFamily
from aqumenlib.instruments.xccy_family import CrossCurrencySwapFamily
import pytest

from aqumenlib import (
    Date,
    Currency,
    MarketView,
    RateInterpolationType,
)
from aqumenlib.calendar import Calendar
from aqumenlib import indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
    add_bootstraped_rate_curve_to_market,
    add_bootstraped_xccy_discounting_curve_to_market,
)


def make_euraud_domestic_model(
    pricing_date: Date,
    dom_fwd: float,
    dom_dsc: float,
    frn_fwd: float,
    frn_dsc: float,
):
    """
    Create a market view where purely domestic instruments
    are used to build discount and forward curves for EUR and AUD.
    EUR is considered domestic, and forward and discount rates are given;
    AUD is considered foreign.
    """
    market = MarketView(name="test model", pricing_date=pricing_date)
    curve_estr = add_bootstraped_discounting_rate_curve_to_market(
        name="ESTR Curve",
        market=market,
        instruments=[
            create_instrument("IRS-ESTR-1Y", dom_dsc),
            create_instrument("IRS-ESTR-10Y", dom_dsc),
        ],
        rate_index=indices.ESTR,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_euribor3m = add_bootstraped_rate_curve_to_market(
        name="EURIBOR3M Curve",
        market=market,
        instruments=[
            create_instrument("IRS-EURIBOR3M-1Y", dom_fwd),
            create_instrument("IRS-EURIBOR3M-10Y", dom_fwd),
        ],
        rate_index=indices.EURIBOR3M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_aonia = add_bootstraped_discounting_rate_curve_to_market(
        name="AONIA Curve",
        market=market,
        instruments=[
            create_instrument("IRS-AONIA-1Y", frn_dsc),
            create_instrument("IRS-AONIA-10Y", frn_dsc),
        ],
        rate_index=indices.AONIA,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_bbsw3m = add_bootstraped_rate_curve_to_market(
        name="BBSW3M Curve",
        market=market,
        instruments=[
            create_instrument("IRS-BBSW3M-1Y", frn_fwd),
            create_instrument("IRS-BBSW3M-10Y", frn_fwd),
        ],
        rate_index=indices.BBSW3M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    return market


def make_eurxaud_xccy_model(market: MarketView, spread: float, spread_on_domestic_leg: bool, rebalance_notionals: bool):
    """
    Create a market view with a cross-currency CSA based AUD
    discount curve based on one where native discount and
    forward curves for EUR and AUD already exist.
    Instruments used are xccy swaps, and spread input determines the quotes.
    EUR is considered domestic currency.
    """
    xfam = CrossCurrencySwapFamily(
        name="EURAUD XCCY swap",
        index_base=indices.EURIBOR3M,
        index_quote=indices.BBSW3M,
        settlement_delay=2,
        calendar=Calendar(ql_calendar_id="TARGET"),
        rebalance_notionals=rebalance_notionals,
        spread_on_base_leg=spread_on_domestic_leg,
    )
    market.add_spot_FX(Currency.EUR, Currency.AUD, 1.7)
    curve_aud_x = add_bootstraped_xccy_discounting_curve_to_market(
        name="AUD XCCY Curve",
        market=market,
        instruments=[
            create_instrument((xfam, "1Y"), spread),
            create_instrument((xfam, "10Y"), spread),
        ],
        target_currency=Currency.AUD,
        target_discounting_id="AUDxEUR",
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    return market


def expected_df_rate(
    dom_fwd: float,
    dom_dsc: float,
    frn_fwd: float,
    frn_dsc: float,  # unused, intentional
    spread: float,
    spread_on_domestic_leg: bool,
):
    """
    Approximate calculation of expected xccy AUD discounting rate
    at one year point.
    """
    frn_s = 0.0 if spread_on_domestic_leg else spread
    dom_s = 0.0 if not spread_on_domestic_leg else spread
    frn_dsc = (1 + dom_dsc) * (1 + frn_fwd + frn_s) / (1 + dom_fwd + dom_s) - 1
    return frn_dsc


def test_eurxaud_csa_model():
    """
    Test curve building for the use case where funds for trading in AUD are raised
    in FX market by using EUR collateral.

    In this situation, EUR DF curve can be built from domestic EUR
    instruments, while discounting curve for AUD should be bootstrapped from
    FX instruments such as FX or cross-currency swaps.

    This test uses cross-currency swaps for curve building.
    """
    # set do_print to True to display results in stdout
    do_print = False
    # test cases setting all 5 rates, and bools for spread on dom leg, rebalance
    test_table = [
        [0.05, 0.05, 0.05, 0.05, 0.001, False, False],
        [0.05, 0.05, 0.05, 0.05, 0.001, False, True],
        [0.05, 0.05, 0.05, 0.05, 0.001, True, True],
        [0.05, 0.05, 0.05, 0.05, 0.01, True, True],
        [0.05, 0.05, 0.05, 0.05, 0.01, False, True],
        [0.05, 0.05, 0.05, 0.05, 0.01, False, False],
        [0.05, 0.05, 0.05, 0.02, 0.01, False, False],
        [0.05, 0.05, 0.05, 0.02, 0.01, False, True],
        [0.05, 0.05, 0.05, 0.09, 0.01, False, False],
        [0.05, 0.05, 0.05, 0.09, 0.01, False, True],
        [0.05, 0.07, 0.05, 0.05, 0.01, False, True],
        [0.05, 0.07, 0.05, 0.05, 0.01, True, True],
        [0.05, 0.07, 0.05, 0.05, 0.01, True, False],
        [0.05, 0.03, 0.05, 0.05, 0.01, False, True],
        [0.03, 0.05, 0.05, 0.05, 0.01, False, True],
        [0.05, 0.05, 0.05, 0.05, 0.01, False, True],
        [0.05, 0.05, 0.07, 0.05, 0.01, False, True],
        [0.05, 0.05, 0.03, 0.05, 0.01, False, True],
    ]
    pricing_date = Date.from_any("2023-11-28")
    results_for_df = []
    for tcase in test_table:
        market = make_euraud_domestic_model(
            pricing_date,
            tcase[0],
            tcase[1],
            tcase[2],
            tcase[3],
        )
        market = make_eurxaud_xccy_model(
            market=market,
            spread=tcase[4],
            spread_on_domestic_leg=tcase[5],
            rebalance_notionals=tcase[6],
        )
        curve_estr = market.get_discounting_curve(Currency.EUR)
        curve_euribor3m = market.get_index_curve(indices.EURIBOR3M)
        curve_aonia = market.get_discounting_curve(Currency.AUD)
        curve_bbsw3m = market.get_index_curve(indices.BBSW3M)
        curve_aud_x = market.get_discounting_curve("AUDxEUR")
        df_dict = {}
        for c in [
            curve_estr,
            curve_euribor3m,
            curve_aonia,
            curve_bbsw3m,
            curve_aud_x,
        ]:
            df_dict[c.get_name()] = f"{100* c.zero_rate(Date.from_isoint(20241128)):.7f}"
        df_dict["Spread"] = f"{100*tcase[4]:.2f}"
        df_dict["Expect"] = f"{100*expected_df_rate(tcase[0], tcase[1], tcase[2], tcase[3], tcase[4], tcase[5]):.2f}"
        df_dict["S Dom"] = f"{tcase[5]}"
        df_dict["Rebal"] = f"{tcase[6]}"
        results_for_df.append(df_dict)
        assert float(df_dict["AUD XCCY Curve"]) == pytest.approx(float(df_dict["Expect"]), abs=0.3)
    if do_print:
        import pandas as pd

        df = pd.DataFrame(results_for_df)
        print(df)


def make_eurxaud_fxswap_model(
    market: MarketView,
    fwd_pts: float,
):
    """
    Create a market view with a cross-currency CSA based AUD
    discount curve based on one where native discount and
    forward curves for EUR and AUD already exist.
    Instruments used are FX swaps, and fwd_pts input determines the quotes.
    EUR is considered domestic currency.
    """
    fxfam = FXSwapFamily(
        name="EURAUD FX swap",
        currency_base=Currency.EUR,
        currency_quote=Currency.AUD,
        settlement_delay=2,
        calendar=Calendar(ql_calendar_id="TARGET"),
    )

    market.add_spot_FX(Currency.EUR, Currency.AUD, 1.7)
    curve_aud_x = add_bootstraped_xccy_discounting_curve_to_market(
        name="AUD XCCY Curve",
        market=market,
        instruments=[
            create_instrument((fxfam, "1Y"), fwd_pts),
        ],
        target_currency=Currency.AUD,
        target_discounting_id="AUDxEUR",
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    return market


def expected_df_rate_from_fxswap(
    dom_dsc: float,
    fx0: float,
    fwd_points: float,
):
    """
    Approximate calculation of expected xccy AUD discounting rate
    at one year point.
    """
    frn_dsc = (1 + dom_dsc) * (1 + fwd_points / fx0) - 1
    return frn_dsc


def test_eurxaud_fx_model():
    """
    This is like test_eurxaud_csa_model() but
    this test uses FX swaps for curve building.
    """
    # set do_print to True to display results in stdout
    do_print = True
    # test cases setting domestic rate and fwd points quote
    test_table = [
        [0.05, 0.01],
        [0.02, 0.001],
        [0.07, 0.02],
        [0.1, 0.01],
        [0.01, 0.001],
        [0.05, -0.01],
        [0.05, -0.05],
    ]
    pricing_date = Date.from_any("2023-11-28")
    results_for_df = []
    for tcase in test_table:
        market = make_euraud_domestic_model(
            pricing_date,
            tcase[0],
            tcase[0],
            tcase[0],
            tcase[0],
        )
        market = make_eurxaud_fxswap_model(
            market=market,
            fwd_pts=tcase[1],
        )
        curve_estr = market.get_discounting_curve(Currency.EUR)
        curve_aud_x = market.get_discounting_curve("AUDxEUR")
        one_year = Date.from_isoint(20241128)
        df_dict = {}
        for c in [
            curve_estr,
            curve_aud_x,
        ]:
            df_dict[c.get_name()] = f"{100* c.zero_rate(one_year):.5f}"
        df_dict["Fwd pts"] = f"{tcase[1]:.5f}"
        fx1 = market.get_fwd_FX(one_year, Currency.EUR, Currency.AUD, csa1=None, csa2="AUDxEUR")
        df_dict["FX fwd"] = f"{fx1:.5f}"
        df_dict["Expect"] = f"{100*expected_df_rate_from_fxswap(tcase[0],1.7,tcase[1]):.5f}"
        results_for_df.append(df_dict)
        assert float(df_dict["AUD XCCY Curve"]) == pytest.approx(float(df_dict["Expect"]), abs=0.3)
    if do_print:
        import pandas as pd

        df = pd.DataFrame(results_for_df)
        print(df)
