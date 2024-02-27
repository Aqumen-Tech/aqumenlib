## Getting started with AQumen SDK

In this guide we will cover the very basics of how the code
is structured and which concepts are used to get to pricing and risk metrics.
We will use a simple bond pricing example which will be sufficient
to introduce the key concepts and how they work together. That should
equip you with the insight necessary to dive into the code and figure
out the rest. While a couple of basic exapmles are included at the 
top level as Jupyter notebooks, many of the test files act as examples
as well, and therefore that is a good place to look after you are finished 
with this tutorial.

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
users with a very simple setup.

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
readable date representations, like ISO strings or integers that mimic them (e.g. 20231117).
Note that evaluation date is part of the market view as well.

The view itself can be created directly by constructing MarketView class,
or by using a utility create_market_view(). Pydantic is used throughout
the library and most classes are Pydantic data classes. This allows for extensive
data validation and also makes all AQumen objects fully serialization to JSON.

Pydantic also allows us to make  the functions API highly flexible in terms of
input, and perform necessary conversions on the fly. For example, we did not
have to pass in a fully Date object to create_market_view function, and we could
instead write this:


```
market = create_market_view("2023-11-17")
```

Next thing one needs to to model discounting and perhaps some indices
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
list_objects() functions; and adding more built-in instruments
is straightforward as well.

The structure behind instruments is layered, with most functionality
encapsulated in InstrumentFamily class hierarchy which
represents a family of instruments, such as all SOA futures or
all fixed-floating SONIA swaps. By combining them with maturity
information, such as 1Y or M25, you get an InstrumentType.
When you add an actual quote, Instrument object is created which
is ready to be used in curve calibrations.

As with MarketView, utility function create_instrument()
can perform necessary conversions, look up built in instruments
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

trade_info=TradeInfo(amount=1_000_000, is_receive=True) 

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

```

### Risk, scenario analysis and beyond






