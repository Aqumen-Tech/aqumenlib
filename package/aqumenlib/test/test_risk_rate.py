# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Test interest rate sensitivity calculations
"""
from aqumenlib.curves.rate_curve import add_bootstraped_discounting_rate_curve_to_market
from aqumenlib.instrument import create_instrument
import pytest
from aqumenlib import Currency, Date, MarketView, indices
from aqumenlib.enums import RiskType, RateInterpolationType
from aqumenlib.pricer import set_global_reporting_currency

from aqumenlib.risk import calculate_market_risk
from aqumenlib.test.test_bond import make_uk_gilt_pricer


def test_uk_gilt_market_risk_swaps():
    """
    Test sensitivity calcs using a UK Gilt with IRS instruments
    """
    set_global_reporting_currency(Currency.GBP)
    test_pricer = make_uk_gilt_pricer()
    pv_before = test_pricer.model_value()

    for in_place in [False, True]:
        risk_ladder = calculate_market_risk(pricers=[test_pricer], in_place_bumps=in_place)
        row = list(filter(lambda x: x.instrument == "IRS-SONIA-30Y", risk_ladder.rows))
        assert len(row) == 1
        assert row[0].risk == pytest.approx(0.0)
        row = list(filter(lambda x: x.instrument == "IRS-SONIA-10Y", risk_ladder.rows))
        assert len(row) == 1
        assert row[0].risk == pytest.approx(-6891919.55, rel=1e-5)
        dv01 = risk_ladder.total_for_risk_type(RiskType.RATE, test_pricer.bond.bond_type.currency)
        assert dv01 == pytest.approx(-7170302.34, abs=10.0)
        pv_after = test_pricer.model_value()
        assert pv_before == pytest.approx(pv_after, rel=1e-9)
        if not in_place:
            assert pv_before == pv_after


def test_uk_gilt_market_risk_futures():
    """
    Test sensitivity calcs using a UK Gilt with futures instruments
    """
    set_global_reporting_currency(Currency.GBP)
    pricing_date = Date.from_any("2013-05-28")
    market = MarketView(name="test model", pricing_date=pricing_date)
    add_bootstraped_discounting_rate_curve_to_market(
        name="SONIA Curve",
        market=market,
        instruments=[
            create_instrument(("FUT-ICE-SOA", "G14"), 100 - 4.0),
            create_instrument(("FUT-ICE-SOA", "K14"), 100 - 4.3),
            create_instrument(("FUT-ICE-SOA", "M14"), 100 - 4.4),
            create_instrument(("FUT-ICE-SOA", "U14"), 100 - 4.7),
            create_instrument(("FUT-ICE-SOA", "V14"), 100 - 4.8),
            create_instrument(("FUT-ICE-SOA", "X14"), 100 - 4.9),
            create_instrument(("FUT-ICE-SOA", "Z14"), 100 - 5.0),
            create_instrument(("FUT-ICE-SOA", "Z23"), 100 - 5.0),
            create_instrument(("FUT-ICE-SOA", "Z33"), 100 - 5.0),
            create_instrument(("FUT-ICE-SOA", "Z43"), 100 - 5.0),
        ],
        rate_index=indices.SONIA,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    test_pricer = make_uk_gilt_pricer(market)
    pv_before = test_pricer.model_value()

    for in_place in [False]:  # TODO in-place bump requires quote handle creation in family
        risk_ladder = calculate_market_risk(pricers=[test_pricer], in_place_bumps=in_place)
        # print(risk_ladder.to_dataframe())
        dv01 = risk_ladder.total_for_risk_type(RiskType.RATE, test_pricer.bond.bond_type.currency)
        assert dv01 == pytest.approx(-7_300_000.0, rel=0.05)
        pv_after = test_pricer.model_value()
        assert pv_before == pytest.approx(pv_after, rel=1e-9)
        if not in_place:
            assert pv_before == pv_after


def test_uk_gilt_market_risk_zcb():
    """
    Test sensitivity calcs using a UK Gilt with zero coupon bond instruments
    """
    set_global_reporting_currency(Currency.GBP)
    pricing_date = Date.from_any("2013-05-28")
    market = MarketView(name="test model", pricing_date=pricing_date)
    add_bootstraped_discounting_rate_curve_to_market(
        name="SONIA Curve",
        market=market,
        instruments=[
            create_instrument(("ZCB-GBP", "5Y"), 0.04),
            create_instrument(("ZCB-GBP", "10Y"), 0.05),
            create_instrument(("ZCB-GBP", "30Y"), 0.05),
        ],
        rate_index=indices.SONIA,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    test_pricer = make_uk_gilt_pricer(market)
    pv_before = test_pricer.model_value()

    for in_place in [False]:  # TODO in-place bump requires quote handle creation in family
        risk_ladder = calculate_market_risk(pricers=[test_pricer], in_place_bumps=in_place)
        print(risk_ladder.to_dataframe())
        dv01 = risk_ladder.total_for_risk_type(RiskType.RATE, test_pricer.bond.bond_type.currency)
        assert dv01 == pytest.approx(-7_300_000.0, rel=0.05)
        pv_after = test_pricer.model_value()
        assert pv_before == pytest.approx(pv_after, rel=1e-9)
        if not in_place:
            assert pv_before == pv_after


def test_relink_market_quote():
    """
    Test that bond price changes as expected when we change market quote.
    """
    set_global_reporting_currency(Currency.GBP)
    test_pricer = make_uk_gilt_pricer()
    pv_before = test_pricer.model_value()
    inst = test_pricer.market.get_instrument("IRS-SONIA-10Y")
    q = inst.get_quote()
    inst.set_quote(q + 1e-4)
    pv_after = test_pricer.model_value()
    expected_diff = -689.1
    assert pv_after - pv_before == pytest.approx(expected_diff, abs=10)
