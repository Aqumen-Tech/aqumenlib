# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Inflation curve building functionality
"""

from typing import Any, List, Tuple
import pydantic

import QuantLib as ql
from aqumenlib import (
    Date,
    DateInput,
    Currency,
    MarketView,
    Instrument,
    Curve,
)

from aqumenlib.index import InflationIndex
from aqumenlib import market_util
from aqumenlib.term import Term


class InflationCurveQL(Curve, pydantic.BaseModel):
    """
    Interest rate curve where underlying representation is a discounting curve
    from which rates are calculated as needed.
    This class relies on QuantLib and uses single curve bootstrap.
    """

    name: str
    index: InflationIndex
    instrument_names: List[str]
    observation_lag: Term

    def model_post_init(self, __context) -> None:
        self._ql_curve: Any = None
        self._base_date: Date = None
        if len(self.instrument_names) == 0:
            raise RuntimeError(f"Inflation curve {self.name} does not have any instruments specified")

    def __str__(self):
        return f"InflationCurve(name={self.name})"

    def get_name(self):
        """
        Curve ID
        """
        return self.name

    def get_currency(self) -> Currency:
        """
        Currency of the index
        """
        return self.index.get_currency()

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
        return self.instrument_names

    def get_prerequisite_curve_ids(self) -> List[str]:
        return []

    def value(self, dt: Date) -> float:
        """
        Compute curve value for a given date
        """
        # TODO this should return projected RPI, not rate
        ql.Settings.instance().setEvaluationDate(self._base_date.to_ql())
        dt = Date.from_any(dt)
        zero_rate = self._ql_curve.zeroRate(dt.to_ql())
        return zero_rate

    def build(self, market: MarketView):
        """
        Bootstrap the curve and generate QuantLib representation
        """
        market.ql_set_pricing_date()
        self._base_date = market.pricing_date
        build_instruments = [market.get_instrument(i) for i in self.instrument_names]
        ql_instruments = []
        for inst in build_instruments:
            ql_helper = inst.inst_type.family.create_ql_instrument(
                market=market,
                quote_handle=inst.get_quote_hanlde(),
                term=inst.inst_type.specifics,
            )
            ql_instruments.append(ql_helper)
        base_rate = build_instruments[0].get_quote()
        qdate = market.pricing_date.to_ql()
        ql_index = self.index.ql_index.clone(ql.ZeroInflationTermStructureHandle())
        market_util.add_fixings_to_ql_index(market, self.index.get_name(), ql_index)
        curve = ql.PiecewiseZeroInflation(
            qdate,
            self.index.get_ql_index().fixingCalendar(),
            ql.Actual365Fixed(),
            self.observation_lag.to_ql(),
            ql_index.frequency(),
            base_rate,
            ql_instruments,
            1.0e-10,
            ql.Linear(),
        )
        curve.enableExtrapolation()
        self._ql_curve = curve


def add_inflation_curve_to_market(
    name: str,
    market: MarketView,
    index: InflationIndex,
    observation_lag: Term,
    fixings: List[Tuple[DateInput, float]],
    instruments: List[Instrument],
) -> Curve:
    """
    Bootstraps a zero inflation curve and adds it to market.
    """
    for inst in instruments:
        market.add_instrument(inst)
    inst_names = [i.name for i in instruments]
    #
    curve = InflationCurveQL(
        name=name,
        index=index,
        observation_lag=observation_lag,
        instrument_names=inst_names,
    )
    #
    market.add_index_fixings(index, fixings)
    curve.build(market)
    market.add_index_curve(index, curve)
    return curve
