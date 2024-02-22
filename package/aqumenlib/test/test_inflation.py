# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Tests for inflation products
"""
import pytest
import QuantLib as ql

from aqumenlib import (
    Date,
    Currency,
    MarketView,
    Instrument,
    BusinessDayAdjustment,
    Frequency,
    QuoteConvention,
    Metric,
    AssetClass,
    RiskType,
    TradeInfo,
)
from aqumenlib.bond_type import BondType
from aqumenlib.calendar import Calendar

from aqumenlib.curves.inflation_curve import add_inflation_curve_to_market
from aqumenlib.curves.rate_curve import add_bootstraped_discounting_curve_to_market
from aqumenlib.daycount import DayCount
from aqumenlib.enums import RateInterpolationType
from aqumenlib.instrument_type import InstrumentType
from aqumenlib.instruments.inflation import InflationZeroCouponSwapFamily
from aqumenlib import indices
from aqumenlib.pricers.bond_pricer import BondPricer
from aqumenlib.products.bond import Bond
from aqumenlib.risk import calculate_market_risk
from aqumenlib.term import Term


def test_inflation_curve():
    """
    Test inflation curve building
    """
    ukrpi_fam = InflationZeroCouponSwapFamily(
        name="InflationZCS-UKRPI",
        index=indices.UKRPI,
        day_count=DayCount.ACTACT_ISDA,
        observation_lag=Term.from_str("2M"),
        payment_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
        calendar=Calendar(ql_calendar_id="UnitedKingdom"),
    )
    # _tenors = [ql.Period(y, ql.Years) for y in range(1, 31)]
    fix_sched = ql.Schedule(
        Date.from_any("2007-07-20").to_ql(),
        Date.from_any("2009-11-20").to_ql(),
        ql.Period(1, ql.Months),
        ql.UnitedKingdom(),
        ql.ModifiedFollowing,
        ql.Unadjusted,
        ql.DateGeneration.Backward,
        False,
    )
    fix_dates = [Date.from_ql(d) for d in fix_sched]
    fix_levels = [
        206.1,
        207.3,
        208.0,
        208.9,
        209.7,
        210.9,
        209.8,
        211.4,
        212.1,
        214.0,
        215.1,
        216.8,
        216.5,
        217.2,
        218.4,
        217.7,
        216,
        212.9,
        210.1,
        211.4,
        211.3,
        211.5,
        212.8,
        213.4,
        213.4,
        213.4,
        214.4,
    ]
    fix_data = list(zip(fix_dates, fix_levels))

    market = MarketView(name="test inflation", pricing_date=Date.from_any("2009-11-25"))
    _df_curve = add_bootstraped_discounting_curve_to_market(
        name="GBP DF Zero Curve",
        market=market,
        instruments=[
            Instrument.from_type("ZCB-GBP-1Y", 0.05),
            Instrument.from_type("ZCB-GBP-25Y", 0.05),
        ],
        currency=Currency.GBP,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    quotes = [
        (2010, 3.0495),
        (2011, 2.93),
        (2012, 2.9795),
        (2013, 3.029),
        (2014, 3.1425),
        (2015, 3.211),
        (2016, 3.2675),
        (2017, 3.3625),
        (2018, 3.405),
        (2019, 3.48),
        (2021, 3.576),
        (2024, 3.649),
        (2029, 3.751),
        (2034, 3.77225),
        (2039, 3.77),
        (2049, 3.734),
    ]
    instruments = [
        Instrument.from_type(InstrumentType(family=ukrpi_fam, specifics=Term.from_str(f"{q[0] - 2009}Y")), q[1] / 100)
        for q in quotes
    ]

    curve = add_inflation_curve_to_market(
        name="UK RPI Curve",
        market=market,
        index=indices.UKRPI,
        observation_lag=Term.from_str("2M"),
        fixings=fix_data,
        instruments=instruments,
    )

    # print(curve.value(Date.from_any("2009-11-25")))
    # TODO add model_time and test time / date consistency
    # print(curve._ql_curve.zeroRate(1.01))

    rpi_gilt_type = BondType(
        name="Govt-UK-RPI",
        description="UK RPI Gilt",
        currency=Currency.GBP,
        frequency=Frequency.SEMIANNUAL,
        day_count=DayCount.ACT365F,
        settlement_delay=3,
        period_adjust=ql.ModifiedFollowing,
        calendar=Calendar(ql_calendar_id="UnitedKingdom"),
        index=indices.UKRPI,
    )
    rpi_test_gilt = Bond(
        name="test rpi gilt",
        bond_type=rpi_gilt_type,
        effective=Date.from_any("2007-10-02"),
        maturity=Date.from_any("2052-10-02"),
        coupon=0.1,
        inflation_base=206.1,
        inflation_lag=Term.from_str("3M"),
    )
    test_pricer = BondPricer(
        bond=rpi_test_gilt,
        market=market,
        quote=383.04297558,
        quote_convention=QuoteConvention.CleanPrice,
        trade_info=TradeInfo(amount=1e3),
    )
    assert test_pricer.settlement_date() == Date.from_any(20091130)
    assert test_pricer.value() == pytest.approx(3847.1666769647495, abs=1e-5)
    assert test_pricer.standard_yield() == pytest.approx(0.05058136940002442, abs=1e-5)
    assert test_pricer.clean_price() == pytest.approx(383.04297558, abs=1e-5)
    assert test_pricer.dirty_price() == pytest.approx(384.71666769647493, abs=1e-5)
    assert test_pricer.accrued_interest() == pytest.approx(1.6736921164749123, abs=1e-5)
    assert test_pricer.duration_modified() == pytest.approx(21.954772732542136, abs=1e-5)
    assert test_pricer.duration_macaulay() == pytest.approx(22.510023967381287, abs=1e-5)
    assert test_pricer.convexity() == pytest.approx(673.973929886063, abs=1e-5)
    assert test_pricer.zspread() == pytest.approx(0.0011912216558789528, abs=1e-5)

    # print(f"Value: {test_pricer.value()}")
    # print(f"Yield: {test_pricer.standard_yield()}")
    # print(f"IRR: {test_pricer.irr()}")
    # print(f"Clean: {test_pricer.clean_price()}")
    # print(f"Dirty: {test_pricer.dirty_price()}")
    # print(f"Value (model): {test_pricer.model_value()}")
    # print(f"IRR (model): {test_pricer.irr_model()}")
    # print(f"Clean (model): {test_pricer.clean_price_model()}")
    # print(f"Dirty (model): {test_pricer.dirty_price_model()}")
    # print(f"Accrued: {test_pricer.accrued_interest()}")
    # print(f"Duration (Macaulay): {test_pricer.duration_macaulay()}")
    # print(f"Duration (Modified): {test_pricer.duration_modified()}")
    # print(f"Convexity: {test_pricer.convexity()}")
    # print(f"Z-Spread: {test_pricer.zspread()}")
    # print(f"Yield at 100: {test_pricer.price_to_yield(100.0)}")
    # print(f"Yield at 95 : {test_pricer.price_to_yield(95.00)}")
    flows = test_pricer.calculate(Metric.CASHFLOWS).flows
    assert len(flows) == 87
    risk_ladder = calculate_market_risk([test_pricer], in_place_bumps=False)
    # print(risk_ladder.to_dataframe())
    assert len(risk_ladder.rows) == 18
    row = list(filter(lambda x: x.instrument == "ZCB-GBP-25Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(-85052, abs=1000)
    assert row[0].quote == pytest.approx(0.05, abs=1e-9)
    assert row[0].tenor_time == pytest.approx(25, rel=0.01)
    assert row[0].inst_family == "ZCB-GBP"
    assert row[0].asset_class == AssetClass.RATE
    assert row[0].risk_type == RiskType.RATE
    assert row[0].inst_currency == Currency.GBP
    assert row[0].risk_currency == Currency.GBP
    assert row[0].inst_specifics == "25Y"
    row = list(filter(lambda x: x.instrument == "InflationZCS-UKRPI-40Y", risk_ladder.rows))
    assert len(row) == 1
    assert row[0].risk == pytest.approx(53390, abs=1000)
    assert row[0].quote == pytest.approx(0.037340, abs=1e-9)
    assert row[0].tenor_time == pytest.approx(40, rel=0.01)
    assert row[0].inst_family == "InflationZCS-UKRPI"
    assert row[0].asset_class == AssetClass.INFLATION
    assert row[0].risk_type == RiskType.INFLATION
    assert row[0].inst_currency == Currency.GBP
    assert row[0].risk_currency == Currency.GBP
    assert row[0].inst_specifics == "40Y"
    r1 = risk_ladder.total_for_family("InflationZCS-UKRPI")
    r2 = risk_ladder.total_for_risk_type(RiskType.INFLATION, test_pricer.bond.bond_type.currency)
    assert r1 == r2
    assert r1 == pytest.approx(91700.0, abs=100.0)
    r1 = risk_ladder.total_for_family("ZCB-GBP")
    r2 = risk_ladder.total_for_risk_type(RiskType.RATE, test_pricer.bond.bond_type.currency)
    assert r1 == r2
    assert r1 == pytest.approx(-85367, abs=100.0)
