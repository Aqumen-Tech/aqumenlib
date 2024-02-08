# %% [markdown]
# ![Logo](logo2.jpg)
#
# ## Cross-currency CSA discounting using AQumen SDK
#
# In this example we will look at how pricing can be done in the presense of various collateral agreements on trades, which normally are governed legally via a Credit Support Annex (CSA) agreement.
#
# In single currency case, this simply means that fully collaterized trades where the collateral holding account earns interest at some rate C, you should use a discount curve implied by the rate C in order to correctly value such trades. This is fairly simple to do; also in most markets now the risk free rates are becoming the same rates that the collateral accrues at, further trivializing the situation.
#
# So in this notebook, let us a look at a more complicated use case. Let us consider an investor who normally funds their operation in euros, but wishes to make some trades in a foreign currency (say AUD). Such an investor would typically fund his AUD trades by raising money in FX markets, not in the domestic AUD markets. The collateral would be posted in EUR, and corresponding rate like ESTR cannot be used to discount in AUD directly.
#
# Therefore to value AUD trades, one needs to construct a discounting curve in AUD that is built using FX instruments like FX swaps and cross-currency swaps. Let us consider the steps required.
#

# %%
# imports and configuration
"""
Hello-World like intro to AQumen SDK
"""

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
from aqumenlib.schema import quote_db

try:
    from IPython.display import display

    do_display = display
except ImportError:
    do_display = print


# %% [markdown]
# ## Modeling domestic markets
#
# Let us assume that the FX instruments of interest are EUR-AUD FX swaps, and EURIBOR3M-BBSW3M cross currency swaps. In order to value the latter, we need to first model the domestic markets in both EUR and AUD, the way local investors would. This is required for two reasons. First, we will need  projected rates for both EURIBOR3M and BBSW3M, and we get those from local interest rate instruments like IR swaps; those quotes are provided under the assumption of local risk-free rate discounting, so proper local IR model is needed. Second, as an investor you want the local model of AUD market to verify pricing of on-market swaps and understand the impact of funding trades via  FX markets.
#
# So let us create a market view where purely domestic instruments are used to build discount and forward curves for EUR and AUD.

# %%
pricing_date = Date.from_any("2023-11-17")
market = MarketView(name="EURxAUD model", pricing_date=pricing_date)

curve_estr = add_bootstraped_discounting_rate_curve_to_market(
    name="ESTR Curve",
    market=market,
    instruments=[
        create_instrument("IRS-ESTR-1Y", 0.05),
        create_instrument("IRS-ESTR-10Y", 0.05),
    ],
    rate_index=indices.ESTR,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
curve_euribor3m = add_bootstraped_rate_curve_to_market(
    name="EURIBOR3M Curve",
    market=market,
    instruments=[
        create_instrument("IRS-EURIBOR3M-1Y", 0.055),
        create_instrument("IRS-EURIBOR3M-10Y", 0.055),
    ],
    rate_index=indices.EURIBOR3M,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
curve_aonia = add_bootstraped_discounting_rate_curve_to_market(
    name="AONIA Curve",
    market=market,
    instruments=[
        create_instrument("IRS-AONIA-1Y", 0.066),
        create_instrument("IRS-AONIA-10Y", 0.065),
    ],
    rate_index=indices.AONIA,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
curve_bbsw3m = add_bootstraped_rate_curve_to_market(
    name="BBSW3M Curve",
    market=market,
    instruments=[
        create_instrument("IRS-BBSW3M-1Y", 0.07),
        create_instrument("IRS-BBSW3M-10Y", 0.07),
    ],
    rate_index=indices.BBSW3M,
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
