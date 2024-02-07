# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Tests for IR swaps
"""
from typing import List
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
)


def make_market(pricing_date: Date):
    """
    Util to make market view
    """
    market = MarketView(name="test model", pricing_date=pricing_date)
    add_bootstraped_discounting_rate_curve_to_market(
        name="SONIA Curve",
        market=market,
        instruments=[
            Instrument.from_type("IRS-SONIA-1M", 0.03),
            Instrument.from_type("IRS-SONIA-1Y", 0.04),
            Instrument.from_type("IRS-SONIA-10Y", 0.05),
            Instrument.from_type("IRS-SONIA-30Y", 0.07),
        ],
        rate_index=indices.SONIA,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )

    d0 = market.pricing_date.to_excel()
    market.add_index_fixings(
        indices.SOFR,
        [[Date.from_excel(d0 - i), 0.1] for i in range(0, 100)],
    )
    return market


def make_ois_simple_pricer():
    """
    Test simple OIS pricer
    """
    market = make_market(Date.from_any("2023-11-28"))
    set_global_reporting_currency(Currency.GBP)
    ois = InterestRateSwap(
        name="test_ois",
        index=indices.SONIA,
        effective=Date.from_any("2023-11-29"),
        maturity=Date.from_any("2033-11-29"),
        frequency=Frequency.ANNUAL,
        fixed_coupon=0.07,
        fixed_day_count=DayCount.ACT365F,
        payment_calendar=Calendar(ql_calendar_id="UnitedKingdom"),
        period_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
        payment_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
        maturity_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
    )
    test_pricer = InterestRateSwapPricer(
        swap=ois,
        market=market,
        trade_info=TradeInfo(amount=1_000_000, is_receive=False),
    )
    return test_pricer


def test_ois_simple():
    """
    Test simple OIS pricer
    """
    test_pricer = make_ois_simple_pricer()

    assert test_pricer.calculate(Metric.VALUE)[0][0] == Currency.GBP
    assert test_pricer.calculate(Metric.VALUE)[0][1] == pytest.approx(-155147, abs=1)
    assert test_pricer.calculate(Metric.REPORTING_VALUE) == pytest.approx(-155147, abs=1)
    assert test_pricer.par_coupon() == pytest.approx(0.05, abs=1e-5)
    assert test_pricer.par_spread() == pytest.approx(0.02, abs=1e-5)

    cashflows = test_pricer.calculate(Metric.CASHFLOWS)
    flows: List[Cashflow] = cashflows.flows
    print(flows)
    assert len(flows) == 20
    assert flows[0].currency == Currency.GBP
    assert flows[0].date == Date.from_any("2024-11-29")
    assert flows[0].amount == pytest.approx(-70_000.00 * 366 / 365, abs=0.01)
    assert flows[-1].currency == Currency.GBP
    assert flows[-1].date == Date.from_any("2033-11-29")
    assert flows[-1].amount == pytest.approx(51_418.27, abs=1.0)

    risk_ladder = calculate_market_risk([test_pricer])
    print(risk_ladder.to_dataframe())
    row = list(filter(lambda x: x.instrument == "IRS-SONIA-30Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(0.0)
    row = list(filter(lambda x: x.instrument == "IRS-SONIA-10Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(8.447e6, rel=0.01)


def test_ois_roundtrip():
    """
    Test that on-market OIS swap prices to par
    """
    test_pricer = make_ois_simple_pricer()
    test_pricer.swap.fixed_coupon = 0.05
    test_pricer.set_market(test_pricer.market)

    value = test_pricer.calculate(Metric.VALUE)[0]
    assert value[0] == Currency.GBP
    assert value[1] == pytest.approx(0, abs=1e-5)
    assert test_pricer.calculate(Metric.REPORTING_VALUE) == pytest.approx(0, abs=1.01)
    assert test_pricer.par_coupon() == pytest.approx(0.05, abs=1e-5)
    assert test_pricer.par_spread() == pytest.approx(0.0, abs=1e-5)

    cashflows = test_pricer.calculate(Metric.CASHFLOWS)
    flows: List[Cashflow] = cashflows.flows
    assert len(flows) == 20
    assert flows[0].currency == Currency.GBP
    assert flows[0].date == Date.from_any("2024-11-29")
    assert flows[0].amount == pytest.approx(-50_000.00 * 366 / 365, abs=0.01)
    assert flows[-1].currency == Currency.GBP
    assert flows[-1].date == Date.from_any("2033-11-29")
    assert flows[-1].amount == pytest.approx(51_418.27, abs=1.0)

    risk_ladder = calculate_market_risk([test_pricer])
    row = list(filter(lambda x: x.instrument == "IRS-SONIA-30Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(0.0)
    row = list(filter(lambda x: x.instrument == "IRS-SONIA-10Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(7_753_942, rel=0.01)
    row = list(filter(lambda x: x.instrument == "IRS-SONIA-1Y", risk_ladder.rows))
    assert row[0].risk == pytest.approx(0, abs=10)
    row = list(filter(lambda x: x.instrument == "IRS-SONIA-1M", risk_ladder.rows))
    assert row[0].risk == pytest.approx(0, abs=10)


def test_ois_serialize():
    """
    Test swap pricer serialization
    """
    p = make_ois_simple_pricer()
    pricer_json = p.model_dump_json()
    v1 = p.value()
    p2 = InterestRateSwapPricer.model_validate_json(pricer_json)
    v2 = p2.value()
    assert v1 == v2
