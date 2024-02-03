# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
An example showing standard calculations for a fixed coupon bond,
including risk and scenario analysis
"""

from aqumenlib import (
    Date,
    Currency,
    MarketView,
    Instrument,
    Curve,
    QuoteConvention,
    QuoteBumpType,
    RiskType,
    Metric,
    RateInterpolationType,
    TradeInfo,
)
from aqumenlib import indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
)
from aqumen.data_model.quotes import get_quote
from aqumenlib.pricer import set_global_reporting_currency
from aqumenlib.pricers.bond_pricer import BondPricer
from aqumenlib.products.bond import Bond
from aqumenlib.risk import calculate_market_risk
from aqumenlib.scenario import (
    create_adjust_quotes_scenario,
    create_curve_shape_scenario,
    calculate_scenario_impact,
    combine_scenario_results,
)

market = MarketView(name="test model", pricing_date=Date.from_isoint(20231116))
d0 = market.pricing_date.to_excel()


def add_ois_curve(market_view, rate_index, tenors) -> Curve:
    """
    Curve construction heler that fetches quotes from DB
    """
    calibration_instruments = []
    inst_types = [f"IRS-{rate_index.name}-{t}" for t in tenors]
    for instrument_type in inst_types:
        quote = get_quote(date=market.pricing_date, instrument_id=instrument_type)
        inst = Instrument.from_type(instrument_type, quote.quote)
        calibration_instruments.append(inst)
    return add_bootstraped_discounting_rate_curve_to_market(
        name=f"{rate_index} Curve",
        market=market_view,
        instruments=calibration_instruments,
        rate_index=rate_index,
        interpolator=RateInterpolationType.PiecewiseLinearForward,
    )


euribor3m_curve = add_ois_curve(market, indices.EURIBOR3M, ["2Y", "3Y", "5Y", "10Y", "30Y"])
add_ois_curve(market, indices.SONIA, ["3M", "3Y", "5Y", "10Y", "30Y"])
add_ois_curve(market, indices.CORRA, ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "10Y", "30Y"])
add_bootstraped_discounting_rate_curve_to_market(
    name="SOFR Curve",
    market=market,
    instruments=[
        Instrument.from_type("IRS-SOFR-1M", 0.053),
        Instrument.from_type("IRS-SOFR-3M", 0.052),
        Instrument.from_type("IRS-SOFR-6M", 0.051),
        Instrument.from_type("IRS-SOFR-9M", 0.050),
        Instrument.from_type("IRS-SOFR-1Y", 0.049),
        Instrument.from_type("IRS-SOFR-2Y", 0.04215),
        Instrument.from_type("IRS-SOFR-3Y", 0.03873),
        Instrument.from_type("IRS-SOFR-5Y", 0.0361),
        Instrument.from_type("IRS-SOFR-10Y", 0.035),
        Instrument.from_type("IRS-SOFR-30Y", 0.0327),
    ],
    rate_index=indices.SOFR,
    interpolator=RateInterpolationType.PiecewiseLinearForward,
)

market.add_index_fixings(
    indices.SOFR,
    [[Date.from_excel(d0 - i), 0.1] for i in range(0, 100)],
)

# get spot rates
dts = [d0] + [d0 + x for x in [10, 20, 30, 45, 60, 90, 120, 180, 250]] + [d0 + 365 * x for x in range(1, 30)]
dts = [Date.from_excel(d) for d in dts]
print("SOFR Curve:")
sofr_curve = market.get_discounting_curve(Currency.USD)
for d in dts:
    print(
        d,
        sofr_curve.zero_rate(d),
        sofr_curve.forward_rate(d),
        sofr_curve.discount_factor(d),
    )

print("Market instruments:")
for k, v in market.get_instrument_map().items():
    print(v)

bond = Bond(
    name="test bond",
    bond_type="FRN-SOFR",
    # bond_type="Govt-UK",
    effective=Date.from_isoint(20231101),
    maturity=Date.from_isoint(20241101),
    coupon=0.00001,
)
set_global_reporting_currency(bond.bond_type.currency)
pricer = BondPricer(
    bond=bond,
    market=market,
    quote=0.073,
    quote_convention=QuoteConvention.Yield,
    trade_info=TradeInfo(amount=1e6),
)

print(f"Value: {pricer.value()}")
print(f"Yield: {pricer.standard_yield()}")
print(f"IRR: {pricer.irr()}")
print(f"Clean: {pricer.clean_price()}")
print(f"Dirty: {pricer.dirty_price()}")
print(f"Value (model): {pricer.model_value()}")
print(f"IRR (model): {pricer.irr_model()}")
print(f"Clean (model): {pricer.clean_price_model()}")
print(f"Dirty (model): {pricer.dirty_price_model()}")
print(f"Accrued: {pricer.accrued_interest()}")
print(f"Duration (Macaulay): {pricer.duration_macaulay()}")
print(f"Duration (Modified): {pricer.duration_modified()}")
print(f"Convexity: {pricer.convexity()}")
print(f"Z-Spread: {pricer.zspread()}")
print(f"Yield at 100: {pricer.price_to_yield(100.0)}")
print(f"Yield at 95 : {pricer.price_to_yield(95.00)}")
print("Cashflows:")
cf = pricer.calculate(Metric.CASHFLOWS)
print(cf)


risk_ladder = calculate_market_risk([pricer])

print(risk_ladder)
dv01 = risk_ladder.total_for_risk_type(
    rtype=RiskType.RATE,
    currency=bond.bond_type.currency,
)
print(f"Rate DV01: {dv01:,.2f}")


scenario_bump = create_adjust_quotes_scenario(
    name="Curve bump",
    adjustment_type=QuoteBumpType.ABSOLUTE,
    adjustment_value=0.01,
    filter_risk_type=RiskType.RATE,
    filter_currency=pricer.bond.bond_type.currency,
)
scenario_market = scenario_bump.create_market(market)
scenario_bump_pricer = pricer.new_pricer_for_market(scenario_market)

print(f"Scenario analysis: {scenario_bump.name}")
print(f"Baseline: model clean value: {pricer.clean_price_model()}")
print(f"Scenario: model clean value: {scenario_bump_pricer.clean_price_model()}")

impact_bump = calculate_scenario_impact(
    scenario=scenario_bump,
    pricer=pricer,
    metric=Metric.REPORTING_MODEL_VALUE,
)

scenario_steepen = create_curve_shape_scenario(
    name="Curve Steepener",
    adjustment_type=QuoteBumpType.ABSOLUTE,
    adjustment_function=lambda t: t / 30.0 * 0.05,  # steepen by 5% over 30 years
    # filter_instrument_family="IRS-SONIA",
    filter_risk_type=RiskType.RATE,
    filter_currency=pricer.bond.bond_type.currency,
)

impact_steepen = calculate_scenario_impact(
    scenario=scenario_steepen,
    pricer=pricer,
    metric=Metric.REPORTING_MODEL_VALUE,
)
print("Scenario impacts:")
print(combine_scenario_results((impact_bump, impact_steepen)))
