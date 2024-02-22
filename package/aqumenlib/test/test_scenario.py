# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Test scenario analysis
"""
import pytest
from aqumenlib import Currency
from aqumenlib.enums import Metric, QuoteBumpType, RiskType
from aqumenlib.pricer import set_global_reporting_currency
from aqumenlib.scenario import calculate_scenario_impact, create_adjust_quotes_scenario, create_curve_shape_scenario
from aqumenlib.test.test_bond import make_uk_gilt_pricer


def test_uk_gilt_scenario_curve_shift():
    """
    Test scenario calcs using a UK Gilt - curve parallel shift
    """
    set_global_reporting_currency(Currency.GBP)
    test_pricer = make_uk_gilt_pricer()
    pv_before = test_pricer.model_value()
    #
    scenario = create_adjust_quotes_scenario(
        name="Test Scenario",
        adjustment_type=QuoteBumpType.ABSOLUTE,
        adjustment_value=0.0001,
        filter_risk_type=RiskType.RATE,
    )
    scenario_market = scenario.create_market(test_pricer.market)
    scenario_pricer = test_pricer.new_pricer_for_market(scenario_market)

    assert scenario.name == "Test Scenario"
    pv0 = test_pricer.model_value()
    pv1 = scenario_pricer.model_value()
    cv0 = test_pricer.clean_price_model()
    cv1 = scenario_pricer.clean_price_model()
    dv0 = test_pricer.dirty_price_model()
    dv1 = scenario_pricer.dirty_price_model()
    diff1 = pv1 - pv0
    diff2 = cv1 - cv0
    diff3 = dv1 - dv0

    assert diff1 / diff2 == pytest.approx(test_pricer.trade_info.amount / 100, rel=0.01)
    assert diff2 == diff3
    pv_after = test_pricer.model_value()
    assert pv_before == pv_after


def test_uk_gilt_scenario_curve_steepen():
    """
    Test scenario calcs using a UK Gilt - curve steepen
    """
    set_global_reporting_currency(Currency.GBP)
    test_pricer = make_uk_gilt_pricer()
    pv_before = test_pricer.model_value()
    scenario = create_curve_shape_scenario(
        name="Curve Steepener Scenario",
        adjustment_type=QuoteBumpType.ABSOLUTE,
        adjustment_function=lambda t: t / 30.0 * 0.05,  # steepen by 5% over 30 years
        filter_instrument_family="IRS-SONIA",
    )
    impact = calculate_scenario_impact(
        scenario=scenario,
        pricer=test_pricer,
        metric=Metric.REPORTING_MODEL_VALUE,
    )
    assert len(impact.rows) == 1
    impact = impact.rows[0]
    pv_after = test_pricer.model_value()
    assert pv_before == pv_after
    assert impact.base_value == pv_before
    assert impact.value_type == Metric.REPORTING_MODEL_VALUE
    assert impact.change_rel * impact.base_value == pytest.approx(impact.change_abs, rel=1e-5)
    assert impact.change_rel * 100 == pytest.approx(-9.0, abs=1.0)
