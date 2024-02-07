"""
Test construction of interest rate curves and discount curves.
"""
import pytest
from aqumenlib import Currency, Date, Instrument, MarketView, RateInterpolationType, indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_curve_to_market,
    add_bootstraped_rate_curve_to_market,
    add_bootstraped_discounting_rate_curve_to_market,
)
from aqumenlib.daycount import DayCount
from aqumenlib.calendar import Calendar
from aqumenlib.enums import BusinessDayAdjustment, Frequency, RiskType, Metric
from aqumenlib.pricers.irs_pricer import InterestRateSwapPricer
from aqumenlib.products.irs import InterestRateSwap
from aqumenlib.risk import calculate_market_risk
from aqumenlib.trade import TradeInfo


def test_zcb_curve():
    """
    Test curve building via zero rates
    """
    market = MarketView(name="test model", pricing_date=Date.from_isoint(20230810))
    curve = add_bootstraped_discounting_curve_to_market(
        name="EUR Curve",
        market=market,
        instruments=[
            Instrument.from_type("ZCB-EUR-1Y", 0.05),
            Instrument.from_type("ZCB-EUR-5Y", 0.10),
        ],
        currency=Currency.EUR,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    assert curve.zero_rate(Date.from_isoint(20240810)) == pytest.approx(0.05)
    assert curve.zero_rate(Date.from_isoint(20280810)) == pytest.approx(0.10)
    assert curve.discount_factor(Date.from_isoint(20280810)) == pytest.approx(1.0 / 1.1**5, abs=0.001)


def test_libor_discounting():
    """
    Test curve building for LIBOR discounting model.
    """
    market = MarketView(name="test model", pricing_date=Date.from_isoint(20230810))
    curve = add_bootstraped_discounting_rate_curve_to_market(
        name="EUR Curve",
        market=market,
        instruments=[
            Instrument.from_type("IRS-EURIBOR3M-1Y", 0.1),
        ],
        rate_index=indices.EURIBOR3M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    for dt in [20230815, 20240815, 20280810]:
        assert curve.forward_rate(Date.from_isoint(dt), indices.EURIBOR3M) == pytest.approx(0.095, rel=0.01)
    assert curve.discount_factor(Date.from_isoint(20240810)) == pytest.approx(1.0 / 1.1, abs=0.001)


def create_dual_curve_discounting_view() -> MarketView:
    """
    Create a market view for LIBOR/OIS dual curve model.
    """
    market = MarketView(name="test model", pricing_date=Date.from_isoint(20230810))
    curve_estr = add_bootstraped_discounting_curve_to_market(
        name="EUR ESTR DF Curve",
        market=market,
        instruments=[
            Instrument.from_type("IRS-ESTR-10M", 0.001),
            Instrument.from_type("IRS-ESTR-1Y", 0.1),
        ],
        currency=Currency.EUR,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_euribor3m = add_bootstraped_rate_curve_to_market(
        name="EURIBOR3M Curve",
        market=market,
        instruments=[
            Instrument.from_type("IRS-EURIBOR3M-1Y", 0.1),
        ],
        rate_index=indices.EURIBOR3M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    curve_euribor1m = add_bootstraped_rate_curve_to_market(
        name="EURIBOR1M Curve",
        market=market,
        instruments=[
            Instrument.from_type("IRS-EURIBOR1M-EURIBOR3M-1Y", 0.025),
        ],
        rate_index=indices.EURIBOR1M,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    # for c in [curve_estr, curve_euribor3m, curve_euribor1m]:
    #     print(f"{c.get_name()}  {c.zero_rate(Date.from_isoint(20241128))}")
    return market


def test_dual_curve_discounting():
    """
    Test curve building for LIBOR/OIS dual curve model.

    The setup here is to have EURIBOR3M swap at 1Y point quoted at 10%,
    which is used to build a flat projected curve for EURIBOR3M.
    Discounting is with ESTR curve which sits at very low rate for 10M
    then jumps up to very high rate.
    EURIBOR3M swap fixed leg has one cash flow discounted at high rate,
    while float leg has 4 cash flows first 3 of which are discounted at low rate.
    Therefore we expect EURIBOR3M curve to sit lower than the quoted 10% coupon rate,
    as less discounting is applied to it.
    """
    market = create_dual_curve_discounting_view()
    df_curve = market.get_discounting_curve(Currency.EUR)
    euribor3m_curve = market.get_index_curve(indices.EURIBOR3M)
    euribor1m_curve = market.get_index_curve(indices.EURIBOR1M)
    #
    assert df_curve.zero_rate(Date.from_isoint(20230815)) == pytest.approx(0.001, rel=0.03)
    assert df_curve.zero_rate(Date.from_isoint(20240515)) == pytest.approx(0.001, rel=0.03)
    assert df_curve.zero_rate(Date.from_isoint(20240810)) == pytest.approx(0.1, rel=0.03)
    assert df_curve.discount_factor(Date.from_isoint(20240810)) == pytest.approx(1.0 / 1.1, abs=0.0015)
    #
    for dt in [20230815, 20240815, 20280810]:
        assert euribor3m_curve.forward_rate(Date.from_isoint(dt), indices.EURIBOR3M) == pytest.approx(0.0914, rel=0.01)
    #
    for dt in [20230815, 20240815, 20280810]:
        assert euribor1m_curve.forward_rate(Date.from_isoint(dt), indices.EURIBOR1M) == pytest.approx(0.0654, rel=0.01)


def test_dual_curve_discounting_risk():
    """
    Test curve building for LIBOR/OIS dual curve model.
    """
    market = create_dual_curve_discounting_view()

    ois = InterestRateSwap(
        name="test_ois",
        index=indices.EURIBOR1M,
        effective=Date.from_any("2023-11-18"),
        maturity=Date.from_any("2024-11-18"),
        frequency=Frequency.MONTHLY,
        fixed_coupon=0.065,
        fixed_day_count=DayCount.ACT365F,
        payment_calendar=Calendar(ql_calendar_id="UnitedKingdom"),
        period_adjust=BusinessDayAdjustment.FOLLOWING,
        payment_adjust=BusinessDayAdjustment.FOLLOWING,
        maturity_adjust=BusinessDayAdjustment.FOLLOWING,
    )
    test_pricer = InterestRateSwapPricer(
        swap=ois,
        market=market,
        trade_info=TradeInfo(trade_id="OIS pricer", amount=1_000_000, is_receive=False),
    )
    print(test_pricer.calculate(Metric.CASHFLOWS))
    risk_ladder = calculate_market_risk([test_pricer])
    print(risk_ladder)
    dv01 = risk_ladder.total_for_risk_type(rtype=RiskType.RATE, currency=Currency.EUR)
    assert dv01 == pytest.approx(800_000, rel=0.05)
    row = list(filter(lambda x: x.instrument == "IRS-EURIBOR1M-EURIBOR3M-1Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(-950_000, rel=0.05)
