# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
test bond functionality
"""

from typing import List, Optional
import pytest

from aqumenlib import (
    Date,
    Currency,
    MarketView,
    Instrument,
    QuoteConvention,
    Metric,
    RateInterpolationType,
    TradeInfo,
)
from aqumenlib import indices
from aqumenlib.instrument import create_instrument
from aqumenlib.cashflow import Cashflow

from aqumenlib.pricers.bond_pricer import BondPricer
from aqumenlib.products.bond import Bond
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
)


def make_market(pricing_date: Date):
    """
    make test market view
    """
    market = MarketView(name="test model", pricing_date=pricing_date)
    add_bootstraped_discounting_rate_curve_to_market(
        name="SONIA Curve",
        market=market,
        instruments=[
            Instrument.from_type("IRS-SONIA-1M", 0.05),
            Instrument.from_type("IRS-SONIA-1Y", 0.05),
            Instrument.from_type("IRS-SONIA-10Y", 0.05),
            Instrument.from_type("IRS-SONIA-30Y", 0.05),
        ],
        rate_index=indices.SONIA,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )

    d0 = market.pricing_date.to_excel()
    market.add_index_fixings(
        indices.SONIA,
        [[Date.from_excel(d0 - i), 0.1] for i in range(0, 100)],
    )
    return market


def make_uk_gilt_pricer(market: Optional[MarketView] = None) -> BondPricer:
    """
    Create bond pricer for test
    """
    if market is None:
        market = make_market(Date.from_any("2013-05-28"))
    bond = Bond(
        name="test bond",
        bond_type="Govt-UK",
        effective=Date.from_any("1996-02-29"),
        maturity=Date.from_any("2021-06-07"),
        coupon=0.08,
        firstCouponDate=Date.from_any("1996-06-07"),
    )
    test_pricer = BondPricer(
        bond=bond,
        market=market,
        quote=103.0,
        quote_convention=QuoteConvention.CleanPrice,
        trade_info=TradeInfo(amount=1e6),
    )
    return test_pricer


def test_uk_gilt_value():
    """
    Test Gilt pricing.
     Sources of reference prices:
       https://www.dmo.gov.uk/data/gilt-market/historical-prices-and-yields/
       https://github.com/lballabio/QuantLib/blob/master/test-suite/bonds.cpp
    """
    test_pricer = make_uk_gilt_pricer()

    assert test_pricer.settlement_date() == Date.from_any("2013-05-29")
    assert test_pricer.value() == pytest.approx(1068021.978021978)
    assert test_pricer.standard_yield() == pytest.approx(0.07495180296897891)
    assert test_pricer.price_to_yield(103.0) == pytest.approx(0.07495180296897891)
    assert test_pricer.price_to_yield(106.0) == pytest.approx(0.07009195055961609)
    assert test_pricer.clean_price() == pytest.approx(103.0)
    assert test_pricer.dirty_price() == pytest.approx(106.8021978021978)
    assert test_pricer.accrued_interest() == pytest.approx(3.802197802197793)
    assert test_pricer.duration_modified() == pytest.approx(5.676044487668892)
    assert test_pricer.duration_macaulay() == pytest.approx(5.888759371710351)
    assert test_pricer.convexity() == pytest.approx(42.153148915284966)
    assert test_pricer.zspread() == pytest.approx(0.025510081078468142, abs=1e-5)
    # clean/dirty price are calculated as of settlement date
    # whereas pure NPV is discounting to pricing date.
    # here we test this relationship between NPV and clean / dirty price
    dfcurve_gbp = test_pricer.market.get_discounting_curve(Currency.GBP)
    ratio_npv_to_quote_1 = test_pricer.model_value() / test_pricer.dirty_price_model()
    ratio_npv_to_quote_2 = (
        test_pricer.trade_info.amount / 100 * dfcurve_gbp.discount_factor(test_pricer.settlement_date())
    )
    assert ratio_npv_to_quote_1 == pytest.approx(ratio_npv_to_quote_2, rel=1e-5)
    #
    assert test_pricer.calculate(Metric.NATIVE_MARKET_VALUE) == test_pricer.value()
    assert test_pricer.calculate(Metric.NATIVE_MODEL_VALUE) == test_pricer.model_value()
    assert test_pricer.calculate(Metric.RISK_VALUE) == {Currency.GBP: test_pricer.model_value()}
    assert test_pricer.calculate(Metric.VALUE) == {Currency.GBP: test_pricer.market_value()}
    assert test_pricer.calculate(Metric.MODEL_VALUE) == {Currency.GBP: test_pricer.model_value()}
    assert test_pricer.calculate(Metric.CURRENCY) == Currency.GBP
    assert test_pricer.calculate(Metric.IRR) == test_pricer.irr()
    assert test_pricer.calculate(Metric.YIELD) == test_pricer.standard_yield()
    assert test_pricer.calculate(Metric.DURATION) == test_pricer.duration_modified()
    assert test_pricer.calculate(Metric.DURATION_MACAULAY) == test_pricer.duration_macaulay()
    assert test_pricer.calculate(Metric.CONVEXITY) == test_pricer.convexity()
    assert test_pricer.calculate(Metric.ZSPREAD) == test_pricer.zspread()


def test_uk_gilt_cashflows():
    """
    Test cash flow reporting using a UK Gilt
    """
    test_pricer = make_uk_gilt_pricer()

    flows: List[Cashflow] = test_pricer.calculate(Metric.CASHFLOWS).flows
    assert len(flows) == 18
    assert flows[-1].currency == Currency.GBP
    assert flows[-1].date == Date.from_any("2021-06-07")
    assert flows[-1].amount == 1_000_000.00
    assert flows[-2].currency == Currency.GBP
    assert flows[-2].date == Date.from_any("2021-06-07")
    assert flows[-2].amount == pytest.approx(40_000.00, abs=1e-5)
    assert flows[0].currency == Currency.GBP
    assert flows[0].date == Date.from_any("2013-06-07")
    assert flows[0].amount == pytest.approx(40_000.00, abs=1e-5)


def test_frn():
    """
    Test SOFR FRN
    """
    pricing_date = Date.from_ymd(2025, 1, 27)
    market = MarketView(name="test model", pricing_date=pricing_date)
    sofr_curve = add_bootstraped_discounting_rate_curve_to_market(
        name="SOFR Curve",
        market=market,
        instruments=[
            create_instrument(("FUT-ICE-SR1", "G25"), 100 - 4.0),
            create_instrument(("FUT-ICE-SR1", "H25"), 100 - 4.1),
            create_instrument(("FUT-ICE-SR1", "J25"), 100 - 4.2),
            create_instrument(("FUT-ICE-SR1", "K25"), 100 - 4.3),
            create_instrument(("FUT-ICE-SR1", "M25"), 100 - 4.4),
            create_instrument(("FUT-ICE-SR1", "N25"), 100 - 4.5),
            create_instrument(("FUT-ICE-SR1", "Q25"), 100 - 4.6),
            create_instrument(("FUT-ICE-SR1", "U25"), 100 - 4.7),
            create_instrument(("FUT-ICE-SR1", "V25"), 100 - 4.8),
            create_instrument(("FUT-ICE-SR1", "X25"), 100 - 4.9),
            create_instrument(("FUT-ICE-SR1", "Z25"), 100 - 5.0),
            create_instrument(("FUT-ICE-SR1", "H26"), 100 - 5.25),
            create_instrument(("FUT-ICE-SR1", "K26"), 100 - 5.35),
            create_instrument(("FUT-ICE-SR1", "M26"), 100 - 5.5),
            create_instrument(("FUT-ICE-SR1", "U26"), 100 - 5.6),
            create_instrument(("FUT-ICE-SR1", "X26"), 100 - 5.7),
            create_instrument(("FUT-ICE-SR1", "Z26"), 100 - 6.0),
            create_instrument(("FUT-ICE-SR1", "F27"), 100 - 6.0),
            create_instrument(("FUT-ICE-SR1", "Z27"), 100 - 7.0),
            create_instrument(("FUT-ICE-SR1", "Z28"), 100 - 7.0),
        ],
        rate_index=indices.SOFR,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    d0 = market.pricing_date.to_excel()
    market.add_index_fixings(
        indices.SONIA,
        [[Date.from_excel(d0 - i), 0.043] for i in range(0, 100)],
    )
    # pd_e = pricing_date.to_excel()
    # for i in range(1,48):
    #     d = Date.from_excel(pd_e + i * 7)
    #     print(d, sofr_curve.forward_rate(d, indices.SOFR))
    bond = Bond(
        name="test bond",
        bond_type="FRN-SOFR",
        effective=Date.from_ymd(2025, 1, 29),
        maturity=Date.from_ymd(2028, 1, 27),
        coupon=0.0001,
    )
    frn_pricer = BondPricer(
        bond=bond,
        market=market,
        quote=100.0,
        quote_convention=QuoteConvention.CleanPrice,
        trade_info=TradeInfo(amount=1e6),
    )
    cflows = frn_pricer.calculate(Metric.CASHFLOWS)
    print(cflows)
    flows = cflows.flows
    assert flows[0].currency == Currency.USD
    assert flows[0].date == Date.from_any("2026-01-27")
    assert flows[0].rate == pytest.approx(0.046, rel=1e-2)
    assert flows[0].amount == pytest.approx(46_450, rel=1e-2)
    v = frn_pricer.calculate(Metric.MODEL_VALUE)
    assert v[Currency.USD] == pytest.approx(1e6, abs=100)
