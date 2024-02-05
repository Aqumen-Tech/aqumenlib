# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Interest rate curve building functionality
"""

from typing import List, Optional
import pydantic

import QuantLib as ql
from aqumenlib import (
    Date,
    Currency,
    RateIndex,
    MarketView,
    Instrument,
    Curve,
    RateInterpolationType,
)


class BootstrappedRateCurveQL(Curve, pydantic.BaseModel):
    """
    Interest rate curve where underlying representation is a discounting curve
    from which rates are calculated as needed.
    This class relies on QuantLib and uses single curve bootstrap.
    """

    name: str
    currency: Currency
    instrument_ids: List[str]
    interpolator: RateInterpolationType = RateInterpolationType.PiecewiseLogLinearDiscount
    target_index: Optional[RateIndex] = None
    discounting_id: Optional[str] = None
    prerequisite_curve_ids: List[str] = []

    def model_post_init(self, __context) -> None:
        self._ql_curve: ql.YieldTermStructure = None
        self._base_date: Date = None

    def get_name(self):
        return self.name

    def get_ql_curve(self) -> ql.YieldTermStructure:
        return self._ql_curve

    def reset(self):
        """
        Remove all internal configuration specific to a particular market view.
        """
        self._ql_curve: ql.YieldTermStructure = None
        self._base_date: Date = None

    def is_built(self) -> bool:
        """
        Check if this curve has been calibrated.
        """
        return self._ql_curve is not None

    def get_prerequisite_instrument_ids(self) -> List[str]:
        return self.instrument_ids

    def get_prerequisite_curve_ids(self) -> List[str]:
        return list(self.prerequisite_curve_ids)

    def zero_rate(self, dt: Date) -> float:
        """
        Compute zero (aka spot) interest rate for a given date
        """
        ql.Settings.instance().setEvaluationDate(self._base_date.to_ql())
        if not isinstance(dt, Date):
            dt = Date.from_py(dt)
        dc = ql.Actual365Fixed()
        compounding = ql.Compounded
        freq = ql.Annual
        zero_rate = self._ql_curve.zeroRate(dt.to_ql(), dc, compounding, freq)
        return zero_rate.rate()

    def forward_rate(self, dt: Date, index: Optional[RateIndex] = None) -> float:
        """
        Compute instantenuous forward rate for a given date
        """
        ql.Settings.instance().setEvaluationDate(self._base_date.to_ql())
        if not isinstance(dt, Date):
            dt = Date.from_py(dt)
        term = ql.Period(1, ql.Days) if index is None else index.tenor.to_ql()
        dc = ql.Actual365Fixed() if index is None else index.day_count.to_ql()
        d0 = dt.to_ql()
        d1 = d0 + term
        compounding = ql.Simple
        freq = ql.Daily if index is None else index.tenor.to_ql().frequency()
        fwd_rate = self._ql_curve.forwardRate(d0, d1, dc, compounding, freq, True)
        return fwd_rate.rate()

    def discount_factor(self, dt: Date) -> float:
        """
        Compute discount factor at a given future date
        """
        ql.Settings.instance().setEvaluationDate(self._base_date.to_ql())
        if not isinstance(dt, Date):
            dt = Date.from_py(dt)
        return self._ql_curve.discount(dt.to_ql())

    def build(self, market: MarketView):
        """
        Perform calibration of this curve. This should not be called by the users directly.
        """
        market.ql_set_pricing_date()
        self._base_date = market.pricing_date
        build_instruments = [market.get_instrument(i) for i in self.instrument_ids]
        ql_instruments = ql.RateHelperVector()
        for inst in build_instruments:
            ql_helper = inst.inst_type.family.create_ql_instrument(
                market=market,
                quote_handle=inst.get_quote_hanlde(),
                term=inst.inst_type.specifics,
                discounting_id=self.discounting_id,
                target_index=self.target_index,
            )
            ql_instruments.push_back(ql_helper)
        qdate = market.pricing_date.to_ql()
        dc = ql.Actual365Fixed()
        ql_func = getattr(ql, self.interpolator.name)
        bstrap = ql.IterativeBootstrap()
        yield_curve = ql_func(qdate, ql_instruments, dc, bstrap)
        yield_curve.enableExtrapolation()
        self._ql_curve = yield_curve


def add_bootstraped_discounting_curve_to_market(
    name: str,
    market: MarketView,
    instruments: List[Instrument],
    currency: Currency,
    interpolator: RateInterpolationType = RateInterpolationType.PiecewiseLogLinearDiscount,
) -> Curve:
    """
    Bootstraps a discounting curve and adds it to market.
    The curve is assumed to not correspond to any rate index, i.e. this could be a bond curve.
    To use discounting based on an index like SOFR, use add_bootstraped_discounting_rate_curve_to_market.
    """
    for inst in instruments:
        market.add_instrument(inst)
    inst_names = [i.name for i in instruments]
    #
    curve = BootstrappedRateCurveQL(
        name=name,
        currency=currency,
        instrument_ids=inst_names,
        interpolator=interpolator,
    )
    curve.build(market)
    market.add_discount_curve(currency, curve)
    return curve


def add_bootstraped_discounting_rate_curve_to_market(
    name: str,
    market: MarketView,
    instruments: List[Instrument],
    rate_index: RateIndex,
    interpolator: RateInterpolationType = RateInterpolationType.PiecewiseLogLinearDiscount,
) -> Curve:
    """
    Bootstraps a discounting rate curve and adds it to market.
    The curve is assumed to correspond to a rate index and also serve as a discount curve.
    """
    for inst in instruments:
        market.add_instrument(inst)
    inst_names = [i.name for i in instruments]
    #
    curve = BootstrappedRateCurveQL(
        name=name,
        currency=rate_index.get_currency(),
        instrument_ids=inst_names,
        interpolator=interpolator,
    )
    curve.build(market)
    market.add_discount_curve(rate_index.get_currency(), curve)
    market.add_index_curve(rate_index, curve)
    return curve


def add_bootstraped_rate_curve_to_market(
    name: str,
    market: MarketView,
    instruments: List[Instrument],
    rate_index: RateIndex,
    interpolator: RateInterpolationType = RateInterpolationType.PiecewiseLogLinearDiscount,
) -> Curve:
    """
    Bootstraps a rate curve for a given index and adds it to market.
    The discounting curve is external and must already exist in the market.
    """
    for inst in instruments:
        market.add_instrument(inst)
    inst_names = [i.name for i in instruments]
    curve = BootstrappedRateCurveQL(
        name=name,
        currency=rate_index.get_currency(),
        instrument_ids=inst_names,
        interpolator=interpolator,
        target_index=rate_index,
        discounting_id=rate_index.get_currency().name,
    )
    curve.prerequisite_curve_ids = [market.get_discounting_curve(curve.discounting_id).get_name()]
    for inst in instruments:
        for dep_index in inst.get_family().get_underlying_indices():
            if dep_index.get_name() != rate_index.get_name():
                dep_curve = market.get_index_curve(dep_index)
                curve.prerequisite_curve_ids.append(dep_curve.get_name())
    curve.prerequisite_curve_ids = list(set(curve.prerequisite_curve_ids))
    curve.build(market)
    market.add_index_curve(rate_index, curve)
    return curve
