# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
test IR futures pricing and curve building functionality
"""

import pytest
from aqumenlib import (
    Date,
    Currency,
    Metric,
    RateInterpolationType,
    TradeInfo,
)
from aqumenlib.instrument import create_instrument
from aqumenlib.instrument_type import create_instrument_type
from aqumenlib.market import create_market_view
from aqumenlib.pricers.irfuture_pricer import IRFuturePricer
from aqumenlib import indices
from aqumenlib.curves.rate_curve import (
    add_bootstraped_discounting_rate_curve_to_market,
)


def test_irfutures():
    """
    Test IR Futures
    """
    pricing_date = Date.from_ymd(2025, 1, 27)
    market = create_market_view(pricing_date)
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
            create_instrument(("FUT-ICE-SR3", "H26"), 100 - 5.25),
            create_instrument(("FUT-ICE-SR3", "M26"), 100 - 5.35),
            create_instrument(("FUT-ICE-SR3", "U26"), 100 - 5.5),
            create_instrument(("FUT-ICE-SR3", "Z26"), 100 - 5.6),
            create_instrument(("FUT-ICE-SR3", "H27"), 100 - 5.7),
            create_instrument(("FUT-ICE-SR3", "M27"), 100 - 6.0),
            create_instrument(("FUT-ICE-SR3", "U27"), 100 - 6.0),
            create_instrument(("FUT-ICE-SR3", "Z27"), 100 - 7.0),
            create_instrument(("FUT-ICE-SR3", "Z28"), 100 - 7.0),
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
    #     d = Date.from_excel(pd_e + i * 14)
    #     print(d, sofr_curve.forward_rate(d, indices.SOFR))
    contract = create_instrument_type(family="FUT-ICE-SR1", specifics="K25")
    pricer_sr1_k25 = IRFuturePricer(
        contract=contract,
        market=market,
        trade_info=TradeInfo(amount=5, is_receive=False),
        last_settlement_price=95,
        market_price=95.7,
    )
    v = pricer_sr1_k25.calculate(Metric.MARKET_VALUE)
    assert v[Currency.USD] == pytest.approx(-5 * 4167 * 95.7, rel=0.01)
    v = pricer_sr1_k25.calculate(Metric.MODEL_VALUE)
    assert v[Currency.USD] == pytest.approx(-5 * 4167 * 95.7, rel=0.01)
