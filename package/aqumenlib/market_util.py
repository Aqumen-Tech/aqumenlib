# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Modeling functions that do not belong in the MarketView class
"""

from typing import Any
import QuantLib as ql

from aqumenlib.market import MarketView
from aqumenlib.index import RateIndex, InflationIndex


def get_modeled_ql_rate_index(market: MarketView, rate_index: RateIndex) -> ql.IborIndex:
    """
    QuantLib embeds curves and fixings into index objects in order to value products.
    Here we clone a global aQumen index object to generate a QuantLib index for pricers to use.
    """
    curve = market.get_index_curve(rate_index)
    curve_h = ql.YieldTermStructureHandle(curve.get_ql_curve())
    modeled_index = rate_index.get_ql_index().clone(curve_h)
    add_fixings_to_ql_index(market, rate_index.get_name(), modeled_index)
    return modeled_index


def get_modeled_ql_inflation_index(market: MarketView, inf_index: InflationIndex) -> ql.IborIndex:
    """
    QuantLib embeds curves and fixings into index objects in order to value products.
    Here we clone a global aQumen index object to generate a QuantLib index for pricers to use.
    """
    curve = market.get_index_curve(inf_index)
    curve_h = ql.ZeroInflationTermStructureHandle(curve.get_ql_curve())
    modeled_index = inf_index.get_ql_index().clone(curve_h)
    add_fixings_to_ql_index(market, inf_index.get_name(), modeled_index)
    return modeled_index


def add_fixings_to_ql_index(market: MarketView, fixings_name, index: Any) -> None:
    """
    Given a QuantLib index object, extract fixings from the market stored
    under fixings_name (this is normally index name, which cannot be taken from QL object),
    and add the fixings to QuantLib index.

    Note that this function cannot just operate on aqumen Index because QuantLib
    indices get cloned before creation of instruments and pricers, and
    it is the cloned QuantLib indices that need fixings and curves added.
    """
    if fixings_name in market.index_fixings:
        fixings = market.index_fixings[fixings_name]
        for f in fixings:
            index.addFixing(f[0].to_ql(), f[1])
