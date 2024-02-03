# %% [markdown]
# ![Logo](logo2.jpg)
#
# ## INTRODUCTION to aQumen SDK

# %%
# imports and configuration
"""
Hello-World like intro to AQumen SDK
"""
from IPython.display import display
from aqumenlib import (
    Date,
    Frequency,
    BusinessDayAdjustment,
    MarketView,
    QuoteConvention,
    QuoteBumpType,
    RateInterpolationType,
    RiskType,
    Metric,
    TradeInfo,
)
from aqumenlib import indices
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.pricers.bond_pricer import BondPricer
from aqumenlib.instrument import create_instrument
from aqumenlib.products.bond import Bond
from aqumenlib.risk import calculate_market_risk
from aqumenlib.scenario import create_adjust_quotes_scenario
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
)
from aqumenlib.pricers.irs_pricer import InterestRateSwapPricer
from aqumenlib.products.irs import InterestRateSwap
from aqumen.data_model import quotes


# %% [markdown]
# ## Create market view

# %%
pricing_date = Date.from_any("2023-11-17")
market = MarketView(name="Demo model", pricing_date=pricing_date)


# %% [markdown]
# ## Create interest rate curves from OIS swaps

# %%

sonia_curve = add_bootstraped_discounting_rate_curve_to_market(
    name="SONIA Curve",
    market=market,
    rate_index=indices.SONIA,
    instruments=[
        create_instrument("IRS-SONIA-3M", 0.052),
        create_instrument("IRS-SONIA-1Y", 0.05),
        create_instrument("IRS-SONIA-10Y", 0.043),
    ],
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)

quotes.save_quotes(
    instruments=[
        ("IRS-SOFR-1Y", 0.045),
        ("IRS-SOFR-5Y", 0.052),
        ("IRS-SOFR-30Y", 0.057),
    ],
    quote_date=pricing_date,
)

sofr_curve = add_bootstraped_discounting_rate_curve_to_market(
    name="SOFR Curve",
    market=market,
    rate_index=indices.SOFR,
    instruments=quotes.bind_instruments(
        quote_date=pricing_date,
        instrument_types=[
            "IRS-SOFR-1Y",
            "IRS-SOFR-5Y",
            "IRS-SOFR-30Y",
        ],
    ),
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)


# %%
d = Date.from_any(20251126)
print(f"SOFR spot rate at {d} is {sofr_curve.zero_rate(d)}")


# %%
print("Market instruments:")
for k, v in market.get_instrument_map().items():
    print(v.short_str())

# %% [markdown]
# ## Perform valuations

# %%
ust_example = Bond(
    name="Treasury Bond Demo",
    bond_type="Govt-USA",
    effective=Date.from_any("2021-10-25"),
    maturity=Date.from_any("2024-10-25"),
    coupon=0.05,
)
ust_pricer = BondPricer(
    bond=ust_example,
    market=market,
    quote=0.0525,
    quote_convention=QuoteConvention.Yield,
    trade_info=TradeInfo(amount=1_000_000),
)

print(f"Value: {ust_pricer.value():,.2f}")
print(f"Yield: {ust_pricer.standard_yield()}")
print(f"IRR: {ust_pricer.irr()}")
print(f"Clean: {ust_pricer.clean_price()}")
print(f"Dirty: {ust_pricer.dirty_price()}")
print(f"Accrued: {ust_pricer.accrued_interest()}")
print(f"Duration (Macaulay): {ust_pricer.duration_macaulay()}")
print(f"Duration (Modified): {ust_pricer.duration_modified()}")
print(f"Convexity: {ust_pricer.convexity()}")
print(f"Z-Spread: {ust_pricer.zspread()}")
print("Cashflows:")
c = ust_pricer.calculate(Metric.CASHFLOWS)
display(c.to_dataframe())


# %% [markdown]
# ## Compute Market Risk

# %%
risk_ladder = calculate_market_risk([ust_pricer])
display(risk_ladder.to_dataframe())


# %% [markdown]
# ## Scenario Analysis

# %%
scenario = create_adjust_quotes_scenario(
    name="Demo Scenario",
    adjustment_type=QuoteBumpType.ABSOLUTE,
    adjustment_value=-0.01,
    filter_risk_type=RiskType.RATE,
)
scenario_market = scenario.create_market(market)
scenario_pricer = ust_pricer.new_pricer_for_market(scenario_market)

print(f"Baseline model value: {ust_pricer.model_value():,.2f}")
print(f"Scenario model value: {scenario_pricer.model_value():,.2f}")

# %% [markdown]
# ## Swap pricing

# %%

ois = InterestRateSwap(
    name="test_ois",
    index=indices.SONIA,
    effective=Date.from_any("2023-11-18"),
    maturity=Date.from_any("2028-11-18"),
    frequency=Frequency.ANNUAL,
    fixed_coupon=0.041512,
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

print(f"{test_pricer.get_name()} Value: {test_pricer.value():,.2f}")
print(f"{test_pricer.get_name()} Par coupon: {test_pricer.par_coupon():,.6f}")
print(f"{test_pricer.get_name()} Par spread: {test_pricer.par_spread():,.6f}")

risk_ladder = calculate_market_risk([test_pricer], in_place_bumps=True)
display(risk_ladder.to_dataframe())

# %%
c = test_pricer.calculate(Metric.CASHFLOWS)
display(c.to_dataframe())

# %%
