## Getting started with AQumen SDK

In this guide we will cover the all basics that should allow one
to understand which concepts are used to get to pricing
and risk metrics in AQumen SDK. We assume that you have
already followed the installation instructions from the main
README, and that you are comfortable with Python 
as well as financial terminology.

We will use a simple bond pricing example which will be sufficient
to introduce the key concepts and how they work together. That should
equip you with the insight necessary to dive into the code and figure
out the rest. While a couple of basic exapmles are included at the 
top level as Jupyter notebooks, many of the test files act as examples
as well, and therefore that is a good place to look after you are 
finished with this tutorial.

The tutorial is broken into 4 main parts covering modeling the market,
managing market conventions and instrument definitions,
describing trades and pricers, and finally dealing with risk and other
higher level calculations.

### Modeling the market

Before you can value trades and securities, you need to model
the market in some way. Like most modern quant frameworks,
AQumen uses an object that collects and encapsulates as much of
market modeling as is useful to share across multiple trades.
That object is called MarketView, and it stores internally quoted
instruments you use to build the curves, any calibrated curves
(e.g. for discounting or index projection), any fixings etc.
The motivation for aggregating this information in a MarketView
is that it makes subsequent pricing setup much easier for the user,
because once the product is defined, it becomes possible to automatically
pick out the right modeling pieces our of the MarketView, leaving
users with a very simple interface.

So let us look at how one can create a MarketView capable of
pricing fixed income and interest rate trades that only depend
on SONIA rates:

```
pricing_date = Date.from_any("2023-11-17")
market = create_market_view(pricing_date)

sonia_curve = add_bootstraped_discounting_rate_curve_to_market(
    name="SONIA Curve",
    market=market,
    rate_index=indices.SONIA,
    instruments=[
        create_instrument(("FUT-ICE-SOA","G25"), 95.2),
        create_instrument("IRS-SONIA-1Y", 0.05),
        create_instrument("IRS-SONIA-10Y", 0.043),
    ],
    interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
)
```

You will notice that we provide a convenience class called Date that
simplifies a lot of the date manipulation that one has to perform when
dealing with instrument pricing. Among other tools, it provides conversions
from and to QuantLib dates, Excel dates, Python dates as well as a few human
readable date representations, like ISO strings or integers that
mimic them (e.g. 20231117).
Note that evaluation date is part of the market view as well.

The view itself can be created directly by constructing MarketView class,
or by using a utility create_market_view().
[Pydantic](https://docs.pydantic.dev/latest/) is used throughout
the library and most classes are Pydantic data classes. This allows for extensive
data validation and also makes all AQumen objects fully serializable to JSON.

Pydantic also allows us to make  the functions API highly flexible in terms of
input, and perform necessary conversions on the fly. For example, we did not
have to pass in a fully formed Date object to create_market_view function, and we could
instead write this:


```
market = create_market_view("2023-11-17")
```

Next thing one needs to do is model the discounting rates and perhaps some indices
to be projected. In our simple case, we want to use only SONIA index
and use it for discounting as well. A single curve bootstrap like this
in AQumen would normally be handled by a single function
that takes in the instruments to be used in calibration and some
parameters, such as interpolation method which you can pick out
from an enum.

### Instruments and market conventions

You will see that AQumen strives to provide most standard market
conventions as pre-built objects - so that you can use shorthands
like indices.SONIA and refer to instruments by using symbology
that maps to tickers typically found in market data providers like
Bloomberg or Refinitiv - .e.g . "IRS-SONIA-1Y" refers to an interest
rate swap (in this case OIS) with a tenor of 1Y and underlying 
SONIA rate. To see other built-in instruments, you can use
list_objects() function; and adding more built-in instruments
is straightforward as well.

The structure behind instruments is layered, with most functionality
encapsulated in InstrumentFamily class hierarchy where each subclass
represents a family of instruments, such as all SOA futures or
all fixed-floating SONIA swaps. By combining them with maturity
information, such as 1Y or M25, you get an InstrumentType.
When you add an actual quote, Instrument object is created which
is ready to be used in curve calibrations.

As with MarketView, utility function create_instrument()
can perform necessary conversions, look up built-in instruments
or use the instrument object directly. For example, these 
ways of creating an instrument are all valid:

```
create_instrument("IRS-SONIA-1Y", 0.05),
create_instrument(("IRS-SONIA","1Y"), 0.05),

sonia_ois_family = IRSwapFamily( ... )
create_instrument((sonia_ois_family,"1Y"), 0.05),

sonia_ois_1y = InstrumentType(family=sonia_ois_family, specifics="1Y")
create_instrument(sonia_ois_1y, 0.05),
```

as well as creating Instrument class objects directly, of course.

### Products, trades and pricers

AQumen understands and models concepts such as securities, products,
trades and pricers. 

The fundamental structure is that first you define a product, which represents
something that can be repeatedly bought or sold. Aforementioned 1Y SONIA swap
is one example of such product, as well as any security, such as a particular issue
of a goverment bond. It is appropriate to blend product and security into
a single concept within software, since many institutions would treat products and securities
in the same way, often going through explicit securitization process for the products.

Once product is defined, many trades can be created on it using TradeInfo object.
This also captures counterparty information, such as any CSA attached, which in turn
will affect pricing.

Finally, pricer is created to perform actual calculations. 
Pricers are often trivial to create, since unless security-specific  market
information is needed for the pricer, all that you need for valuation is
already contained in the trade and MarketView. 

This is an example of pricing a bond using above concepts:

```
ust_example = Bond(
    name="Treasury Bond Demo",
    bond_type="Govt-USA",
    effective=Date.from_any("2021-10-25"),
    maturity=Date.from_any("2024-10-25"),
    coupon=0.05,
)

trade_info = TradeInfo(amount=1_000_000, is_receive=True)

ust_pricer = BondPricer(
    bond=ust_example,
    market=market,
    quote=0.0525,
    quote_convention=QuoteConvention.Yield,
    trade_info=trade_info,
)

print(f"Value: {ust_pricer.value():,.2f}")
print(f"Yield: {ust_pricer.standard_yield()}")
print(f"IRR: {ust_pricer.irr()}")
print(f"Clean: {ust_pricer.clean_price()}")
print(f"Dirty: {ust_pricer.dirty_price()}")

```

### Risk, scenario analysis and beyond

This is perhaps where the power of AQumen SDK is most obvious.
Because InstrumentFamily objects capture rich meta-data information
about the instruments, and because MarketView keeps track of dependencies
between curves and instruments, to compute market sensitivities
the user does not need to supply any more information or logic, so that
this important market risk calculation can be performed with just one
line of code:

```
risk_ladder = calculate_market_risk([ust_pricer])
```

The outpout is an object that can be readily converted to pandas DataFrame
using to_dataframe() method. It produces tabular output similar to this:

|    | Risk Currency   | Instrument    |    Risk | Family    | Specifics   | Instr Ccy   |   Quote | Asset Class   | Risk Class   |      Time |
|---:|:----------------|:--------------|--------:|:----------|:------------|:------------|--------:|:--------------|:-------------|----------:|
|  3 | USD             | IRS-SOFR-1Y   | -905865 | IRS-SOFR  | 1Y          | USD         |   0.045 | RATE          | RATE         |  1.0137   |
|  4 | USD             | IRS-SOFR-5Y   |       0 | IRS-SOFR  | 5Y          | USD         |   0.052 | RATE          | RATE         |  5.01644  |
|  5 | USD             | IRS-SOFR-30Y  |       0 | IRS-SOFR  | 30Y         | USD         |   0.057 | RATE          | RATE         | 30.0329   |
|  0 | USD             | IRS-SONIA-3M  |       0 | IRS-SONIA | 3M          | GBP         |   0.052 | RATE          | RATE         |  0.260274 |
|  1 | USD             | IRS-SONIA-1Y  |       0 | IRS-SONIA | 1Y          | GBP         |   0.05  | RATE          | RATE         |  1.01096  |
|  2 | USD             | IRS-SONIA-10Y |       0 | IRS-SONIA | 10Y         | GBP         |   0.043 | RATE          | RATE         | 10.0192   |


Note that instruments have classifications and also are labelled with their
pillar information, so that time bucketing becomes easy for the user.

Similarly, scenario analysis is handled by defining scenario
objects that apply to instruments by matching them on any of the available meta-data,
including pillar time, and then applying arbitrary functions or shifts
to associated quotes. Once done, a new MarketView object is produced where
the affected curves are rebuilt, at which point you can re-calculate any metrics
as desired:

```
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
```

To change quotes using arbitrary function as opposed to fixed shift,
use the function create_curve_shape_scenario.

Other utility functions that may be useful are 
calculate_scenario_impact and combine_scenario_results. 


### Moving beyond this tutorial

Take a look at the examples folder at the top level of the GitHub repo
for runnable Jupyter notebooks.

Then jump to test folder under package/aqumenlib/ as many tests are written
in a style that makes them useful as examples or snippets.

Since all of aqumenlib is open source, you are free to navigate around
the code from there, learn about the rest of the structure,
and build your own things where you desire!

