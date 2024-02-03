# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import pytest
from aqumenlib import (
    Date,
    Currency,
    MarketView,
    Instrument,
    RateInterpolationType,
)

from aqumenlib.curves.rate_curve import add_bootstraped_discounting_curve_to_market
from aqumenlib.instrument_type import InstrumentType
from aqumenlib.instruments.zero_coupon import ZeroCouponBondFamily
from aqumenlib.term import Term


def test_fx_rates():
    """
    Test spot FX rates by inversion and triangulation
    """
    market = MarketView(name="test model", pricing_date=Date.from_isoint(20230810))
    market.add_spot_FX(Currency.EUR, Currency.ZAR, 20.52)
    market.add_spot_FX(Currency.EUR, Currency.GBP, 0.859)
    market.add_spot_FX(Currency.EUR, Currency.USD, 1.071)
    assert market.get_spot_FX(Currency.EUR, Currency.USD) == 1.071
    assert market.get_spot_FX(Currency.USD, Currency.EUR) == pytest.approx(0.9337068160597572)
    assert market.get_spot_FX(Currency.USD, Currency.GBP) == pytest.approx(0.8020541549953315)
    assert market.get_spot_FX(Currency.USD, Currency.ZAR) == pytest.approx(19.159663865546218)


def create_zargbp_zcb_market() -> MarketView:
    """
    Market with zero curves for ZAR and GBP, with FX.
    """
    market = MarketView(name="test model", pricing_date=Date.from_isoint(20230810))
    market.add_spot_FX(Currency.EUR, Currency.ZAR, 20.52)
    fam = ZeroCouponBondFamily(name="ZCB-ZAR-test", currency=Currency.ZAR, settlement_delay=2)
    itp = InstrumentType(family=fam, specifics=Term.from_str("5Y"))
    add_bootstraped_discounting_curve_to_market(
        name="ZAR Curve",
        market=market,
        instruments=[Instrument.from_type(itp, 0.10)],
        currency=Currency.ZAR,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    market.add_spot_FX(Currency.EUR, Currency.GBP, 0.859)
    fam = ZeroCouponBondFamily(name="ZCB-GBP-test", currency=Currency.GBP, settlement_delay=2)
    itp = InstrumentType(family=fam, specifics=Term.from_str("5Y"))
    add_bootstraped_discounting_curve_to_market(
        name="GBP Curve",
        market=market,
        instruments=[Instrument.from_type(itp, 0.05)],
        currency=Currency.GBP,
        interpolator=RateInterpolationType.PiecewiseLogLinearDiscount,
    )
    return market


def test_forward_fx_rates():
    """
    Test forward FX rates calculation
    """
    # value 100 ZAR in one year and convert to GBP using spot or forward rate
    market = create_zargbp_zcb_market()
    fwd_date = Date.from_isoint(20240810)
    df_gbp = market.get_discounting_curve(Currency.GBP).discount_factor(fwd_date)
    df_zar = market.get_discounting_curve(Currency.ZAR).discount_factor(fwd_date)
    spot_fx = market.get_spot_FX(Currency.GBP, Currency.ZAR)
    fwd_fx = market.get_fwd_FX(fwd_date, Currency.GBP, Currency.ZAR)
    v1 = 100 * df_zar / spot_fx
    v2 = 100 * df_gbp / fwd_fx
    assert v1 == pytest.approx(expected=3.8046, abs=0.01)
    assert v1 == pytest.approx(v2)
