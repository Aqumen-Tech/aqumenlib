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
    QuoteConvention,
    QuoteBumpType,
    RateInterpolationType,
    RiskType,
    Metric,
    TradeInfo,
    Currency,
    MarketView,
)
from aqumenlib import indices
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.pricers.bond_pricer import BondPricer
from aqumenlib.instrument import create_instrument
from aqumenlib.instruments.fxswap_family import FXSwapFamily
from aqumenlib.instruments.xccy_family import CrossCurrencySwapFamily
from aqumenlib import indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
    add_bootstraped_rate_curve_to_market,
    add_bootstraped_xccy_discounting_curve_to_market,
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
pricing_date = Date.from_any("2024-02-07")
market = MarketView(name="EURxAUD model", pricing_date=pricing_date)

curve_estr = add_bootstraped_discounting_rate_curve_to_market(
    name="ESTR Curve",
    market=market,
    instruments=[
        create_instrument("IRS-ESTR-1Y", 0.0293),
        create_instrument("IRS-ESTR-3Y", 0.0272),
        create_instrument("IRS-ESTR-5Y", 0.0260),
        create_instrument("IRS-ESTR-10Y", 0.0269),
        create_instrument("IRS-ESTR-30Y", 0.0265),
    ],
    rate_index=indices.ESTR,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
curve_euribor3m = add_bootstraped_rate_curve_to_market(
    name="EURIBOR3M Curve",
    market=market,
    instruments=[
        create_instrument("IRS-EURIBOR3M-1Y", 0.0298),
        create_instrument("IRS-EURIBOR3M-3Y", 0.0279),
        create_instrument("IRS-EURIBOR3M-5Y", 0.0265),
        create_instrument("IRS-EURIBOR3M-10Y", 0.028),
        create_instrument("IRS-EURIBOR3M-30Y", 0.028),
    ],
    rate_index=indices.EURIBOR3M,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
curve_aonia = add_bootstraped_discounting_rate_curve_to_market(
    name="AONIA Curve",
    market=market,
    instruments=[
        create_instrument("IRS-AONIA-1Y", 0.0419),
        create_instrument("IRS-AONIA-3Y", 0.0376),
        create_instrument("IRS-AONIA-5Y", 0.0378),
        create_instrument("IRS-AONIA-10Y", 0.041),
        create_instrument("IRS-AONIA-30Y", 0.041),
    ],
    rate_index=indices.AONIA,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
curve_bbsw3m = add_bootstraped_rate_curve_to_market(
    name="BBSW3M Curve",
    market=market,
    instruments=[
        create_instrument("IRS-BBSW3M-1Y", 0.040),
        create_instrument("IRS-BBSW3M-3Y", 0.039),
        create_instrument("IRS-BBSW3M-5Y", 0.041),
        create_instrument("IRS-BBSW3M-10Y", 0.043),
        create_instrument("IRS-BBSW3M-30Y", 0.043),
    ],
    rate_index=indices.BBSW3M,
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)


# %% [markdown]
# ## Modeling FX-driven AUD discounting curve
#
# As discussed above, trades funded by raising money in EUR/AUD FX markets and collaterizing in EUR should be valued with an effective AUD discounting curve derived off the EUR rates curves and FX instruments. Here we build such a curve using FX swaps and cross currency swaps:

# %%
market.add_spot_FX(Currency.EUR, Currency.AUD, 1.7)

fxfam = FXSwapFamily(
    name="EURAUD FX swap",
    currency_base=Currency.EUR,
    currency_quote=Currency.AUD,
    settlement_delay=2,
    calendar=Calendar(ql_calendar_id="TARGET"),
)
xfam = CrossCurrencySwapFamily(
    name="EURAUD XCCY swap",
    index_base=indices.EURIBOR3M,
    index_quote=indices.BBSW3M,
    settlement_delay=2,
    calendar=Calendar(ql_calendar_id="TARGET"),
    rebalance_notionals=True,
    spread_on_base_leg=True,
)

curve_aud_x = add_bootstraped_xccy_discounting_curve_to_market(
    name="AUD XCCY Curve",
    market=market,
    instruments=[
        create_instrument((fxfam, "1M"), 0.0005),
        create_instrument((fxfam, "3M"), 0.0017),
        create_instrument((fxfam, "6M"), 0.0050),
        create_instrument((fxfam, "1y"), 0.0150),
        create_instrument((xfam, "3Y"), 0.001),
        create_instrument((xfam, "10Y"), 0.002),
        create_instrument((xfam, "30Y"), 0.003),
    ],
    target_currency=Currency.AUD,
    target_discounting_id="AUDxEUR",
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)


# %% [markdown]
# ## Checking the resulting curves
#
# Let us print the zero rates on all the resulting curves, which highlights the difference between the native discount curve in AUD and the one built using FX instruments.
#
# We also output the implied forward FX curves, one constructed from the domestic AUD discont curve (labelled as EUR/AUD fwd dom) and one built from FX quotes (labelled EUR/AUD fwd adj). We display these FX curves in forward points.

# %%
rates_for_df = []
pd_e = pricing_date.to_excel()
spot = market.get_spot_FX(Currency.EUR, Currency.AUD)
for i in [1, 3, 6, 9, 12, 24, 36, 5 * 12, 10 * 12, 30 * 12]:
    df_dict = {}
    d = Date.from_excel(pd_e + i * 30)
    df_dict["Date"] = str(d)
    for c in [
        curve_estr,
        curve_euribor3m,
        curve_aonia,
        curve_bbsw3m,
        curve_aud_x,
    ]:
        df_dict[c.get_name()] = f"{100* c.zero_rate(d):.2f}"
    df_dict["EUR/AUD fwd dom"] = 1e4 * (market.get_fwd_FX(d, Currency.EUR, Currency.AUD) - spot)
    df_dict["EUR/AUD fwd adj"] = 1e4 * (market.get_fwd_FX(d, Currency.EUR, Currency.AUD, "EUR", "AUDxEUR") - spot)
    rates_for_df.append(df_dict)

import pandas as pd

df = pd.DataFrame(rates_for_df)
display(df)


# %%
print("Market instruments:")
for k, v in market.get_instrument_map().items():
    print(v.short_str())

# %% [markdown]
# ## Swap pricing - DOMESTIC
#
# Let us first price an on-market swap from the point of view of domestic investor in AUD market:

# %%

ois = InterestRateSwap(
    name="test_ois",
    index=indices.AONIA,
    effective=Date.from_any("2024-02-09"),
    maturity=Date.from_any("2034-02-09"),
    frequency=Frequency.ANNUAL,
    fixed_coupon=0.041,
    fixed_day_count=DayCount.ACT365F,
    payment_calendar=Calendar(ql_calendar_id="Australia"),
    period_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
    payment_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
    maturity_adjust=BusinessDayAdjustment.MODIFIEDFOLLOWING,
)
dom_pricer = InterestRateSwapPricer(
    swap=ois,
    market=market,
    trade_info=TradeInfo(trade_id="AUD domestic pricer", amount=1_000_000, is_receive=False),
)

print(f"{dom_pricer.get_name()} Value: {dom_pricer.value():,.2f}$")
print(f"{dom_pricer.get_name()} Par coupon: {dom_pricer.par_coupon():,.6f}")

# %% [markdown]
# ## SWAP PRICING - FOREIGN
#
# Now let us value the same swap from the point of Europe-based investor who funds his trades from EUR.
# Because the fixed and the floating legs are perfectly balanced, one expects to find that even with a different discount curve the price remains roughly zero.

# %%

forn_pricer = InterestRateSwapPricer(
    swap=ois,
    market=market,
    trade_info=TradeInfo(trade_id="AUD pricer xEUR", amount=1_000_000, is_receive=False, csa_id="AUDxEUR"),
)

print(f"{forn_pricer.get_name()} Value: {forn_pricer.value():,.2f}$")
print(f"{forn_pricer.get_name()} Par coupon: {forn_pricer.par_coupon():,.6f}")

# %% [markdown]
# ## SWAP PRICING - OFF MARKET
#
# Now let us value a pricer that is significantly off-market. We will set fixed coupon rate to 1bps to get a better feel for the effect of changing the discount curve on valuation of fixed income instruments.

# %%
ois.fixed_coupon = 0.0001
dom_pricer.reset()
forn_pricer.reset()

print(f"{dom_pricer.get_name()} Value: {dom_pricer.value():,.2f}$")
print(f"{dom_pricer.get_name()} Par coupon: {dom_pricer.par_coupon():,.6f}")
print(f"{forn_pricer.get_name()} Value: {forn_pricer.value():,.2f}$")
print(f"{forn_pricer.get_name()} Par coupon: {forn_pricer.par_coupon():,.6f}")

# %%
