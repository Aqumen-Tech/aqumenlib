# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
MarketView class
"""

import copy
from dataclasses import dataclass
from typing import List, Dict, Tuple, Self, Optional, Any
from collections import defaultdict
import pydantic

import QuantLib as ql

from aqumenlib import Date, DateInput, Currency, Instrument, Index
from aqumenlib.curve import Curve, get_curve_class_by_name
from aqumenlib.exception import AqumenException
from aqumenlib.instrument import InstrumentFilter


class MarketView(pydantic.BaseModel):
    """
    This class encapsulates information necessary for modeling the market,
    such as quoted instruments, projection curves and fixings.
    """

    name: str
    pricing_date: Date
    # internal state below - all instruments and curves
    instruments: Dict[str, Instrument] = {}
    discount_curves: Dict[str, Curve] = {}
    index_curves: Dict[str, Curve] = {}
    index_fixings: Dict[str, List[Tuple[Date, float]]] = {}
    all_curves: Dict[str, pydantic.SerializeAsAny[Curve]] = {}
    # FX rates
    spot_fx_rates: Dict[Currency, Dict[Currency, float]] = defaultdict(dict)

    def model_post_init(self, __context: Any) -> None:
        self.ql_set_pricing_date()
        # rebuild the curves if necessary - for example if this object was deserialized
        for _, icurve in self.all_curves.items():
            maybe_rebuild_curve(self, icurve)

    def ql_set_pricing_date(self):
        """
        QuantLib relies on some global variables, like pricing date.
        This method will set QuantLib pricing date to that of this market view.
        """
        ql.Settings.instance().setEvaluationDate(self.pricing_date.to_ql())

    def add_instrument(self, instrument: Instrument) -> None:
        """
        Store quoted instrument in this market view.
        """
        if instrument.name in self.instruments:
            if instrument.get_quote() == self.instruments[instrument.name].get_quote():
                pass
            else:
                raise KeyError(f"This market already has instrument {instrument.name} with a different quote")
        self.instruments[instrument.name] = instrument

    def get_instrument_map(self) -> Dict[str, Instrument]:
        """
        Return a map of instrument name to associated object.
        """
        return self.instruments

    def get_instrument(self, instrument_name: str) -> Instrument:
        """
        Look up and return an instrument given name.
        """
        return self.instruments[instrument_name]

    def add_index_fixings(self, index: Index, fixings: List[Tuple[DateInput, float]]) -> None:
        """
        Add fixings for a given index.
        """
        ql_index = index.get_ql_index()
        name = index.get_name()
        if name not in self.index_fixings:
            self.index_fixings[name] = []
        for f in fixings:
            ql_date = f[0].to_ql()
            if ql_index.isValidFixingDate(ql_date):
                self.index_fixings[name].append((f[0], f[1]))

    def get_index_fixings(self, index: Index) -> List[Tuple[Date, float]]:
        """
        Retrive fixings for a given index.
        """
        fixings_name = index.get_name()
        fixings = []
        if fixings_name in self.index_fixings:
            fixings = self.index_fixings[fixings_name]
        return fixings

    def add_discount_curve(self, currency_or_csa: Currency | str, curve: Curve) -> None:
        """
        Add discount curve for a given currency.
        """
        df_id = currency_or_csa.name if isinstance(currency_or_csa, Currency) else currency_or_csa
        if df_id in self.discount_curves:
            raise AqumenException(f"{curve.get_name()}: DF curve already exists in this market.")
        self.discount_curves[df_id] = curve
        #
        if curve.get_name() in self.all_curves and curve != self.all_curves[curve.get_name()]:
            raise AqumenException(f"{curve.get_name()}: curve already exists in this market.")
        self.all_curves[curve.get_name()] = curve

    def get_discounting_curve(self, currency_or_csa: Currency | str) -> Curve:
        """
        Retrive stored discount curve for a given currency.
        """
        df_id = currency_or_csa.name if isinstance(currency_or_csa, Currency) else currency_or_csa
        if df_id not in self.discount_curves:
            raise KeyError(f"Currency or CSA {df_id} does not have discounting curve in this market view.")
        return self.discount_curves[df_id]

    def add_index_curve(self, index: Index, curve: Curve) -> None:
        """
        Add curve for a given index.
        """
        if index.get_name() in self.index_curves:
            raise AqumenException(f"{curve.get_name()}: index curve already exists in this market.")
        self.index_curves[index.get_name()] = curve
        if curve.get_name() in self.all_curves and curve != self.all_curves[curve.get_name()]:
            raise AqumenException(f"{curve.get_name()}: curve already exists in this market.")
        self.all_curves[curve.get_name()] = curve

    def get_index_curve(self, index: Index) -> Curve:
        """
        Find and return a curve for a given Index
        """
        name = index.get_name()
        if name not in self.index_curves:
            raise KeyError(f"Currency {name} does not have a curve configured")
        return self.index_curves[name]

    def add_spot_FX(self, ccy1: Currency, ccy2: Currency, xchange_rate: float):  # pylint: disable=invalid-name
        """
        Adds spot FX rate to market.
        """
        if ccy1 == ccy2:
            raise KeyError("Cannot add FX rate for identical currencies")
        self.spot_fx_rates[ccy1][ccy2] = xchange_rate

    def get_spot_FX(self, ccy1: Currency, ccy2: Currency) -> float:  # pylint: disable=invalid-name
        """
        Returns spot FX rate, performing triangulation or inversion if necessary.
        """
        if ccy1 == ccy2:
            return 1.0
        # first check if this or inverse rate already exist in the dictionary
        if ccy2 in self.spot_fx_rates[ccy1]:
            return self.spot_fx_rates[ccy1][ccy2]
        elif ccy1 in self.spot_fx_rates[ccy2]:
            return 1.0 / self.spot_fx_rates[ccy2][ccy1]
        # otherwise try to triangulate against some other currency
        for iccy, iccy_dict in self.spot_fx_rates.items():
            if ccy1 in iccy_dict and ccy2 in iccy_dict:
                x1 = self.spot_fx_rates[iccy][ccy1]
                x2 = self.spot_fx_rates[iccy][ccy2]
                triangulated_rate = x2 / x1
                self.spot_fx_rates[ccy1][ccy2] = triangulated_rate
                return triangulated_rate
        raise KeyError(f"Market does not contain exchange rate information for {ccy1.name}{ccy2.name}")

    def get_fwd_FX(
        self,
        fwd_date: Date,
        ccy1: Currency,
        ccy2: Currency,
        csa1: Optional[Currency | str] = None,
        csa2: Optional[Currency | str] = None,
    ) -> float:  # pylint: disable=invalid-name
        """
        Returns forward FX rate, performing triangulation or inversion if necessary.

        If only currencies are provided, default discount curves for those currencies are used.
        If CSA-differentiated discounting is necessary, csa1 and csa2 arguments can be
        used to select appropriate discount curves for projecting forward FX.
        """
        if ccy1 == ccy2:
            return 1.0
        dfc1 = csa1 if csa1 is not None else ccy1
        dfc2 = csa2 if csa2 is not None else ccy2
        df1 = self.get_discounting_curve(dfc1).discount_factor(fwd_date)
        df2 = self.get_discounting_curve(dfc2).discount_factor(fwd_date)
        return self.get_spot_FX(ccy1, ccy2) * df1 / df2

    def get_curve_by_name(self, curve_name: str) -> Optional[Curve]:
        """
        Return a curve by curve ID, if exists; otherwise return None.
        """
        if curve_name in self.all_curves:
            return self.all_curves[curve_name]
        return None

    def get_all_curves(self) -> Dict[str, Curve]:
        """
        Returns a name-curve dictionary of all curves within this view.
        """
        return self.all_curves

    def clear_curves(self):
        """
        Remove all curves from this view.
        """
        self.discount_curves = {}
        self.index_curves = {}
        self.all_curves = {}

    def new_market_for_instruments(self, new_instruments: List[Instrument]) -> Self:
        """
        Create a new market where some instruments are replaced by new instruments.
        """
        change_inst_set = set(i.get_name() for i in new_instruments)
        new_market: MarketView = copy.copy(self)
        new_inst_dict = copy.copy(self.instruments)
        for inew_inst in new_instruments:
            new_inst_dict[inew_inst.name] = inew_inst
        new_market.instruments = new_inst_dict
        new_market.clear_curves()
        # reset curves in the new view
        for cname, icurve in self.all_curves.items():
            dep_inst_ids = set(get_indirect_curve_instruments(self, icurve))
            new_curve = copy.copy(icurve)
            if change_inst_set.intersection(dep_inst_ids):
                new_curve.reset()
            new_market.all_curves[cname] = new_curve
        for df_id, icurve in self.discount_curves.items():
            new_market.add_discount_curve(df_id, new_market.get_curve_by_name(icurve.get_name()))
        for index_name, icurve in self.index_curves.items():
            new_market.index_curves[index_name] = new_market.get_curve_by_name(icurve.get_name())
        # rebuild the curves if they are invalidated by instrument changes
        for _, icurve in new_market.all_curves.items():
            maybe_rebuild_curve(new_market, icurve)
        return new_market

    def get_bumped_markets(
        self,
        filter_instrument: Optional[InstrumentFilter] = None,
    ) -> List["BumpedInstrumentMarket"]:
        """
        Bumps each instrument within a MarketView object, and rebuilds the curves.
        """
        markets = []
        for _, inst in self.get_instrument_map().items():
            if filter_instrument is not None and not filter_instrument.matches(inst):
                continue
            bump_size = inst.get_family().get_default_bump()
            new_inst_quote = inst.get_family().bump_quote(inst.quote, bump_size)
            new_inst = Instrument(name=inst.name, inst_type=inst.inst_type, quote=new_inst_quote)
            new_market = self.new_market_for_instruments([new_inst])
            b = BumpedInstrumentMarket(
                instrument=inst,
                market=new_market,
                bump_size=bump_size,
                bump_type=0,
            )
            markets.append(b)
        return markets

    @pydantic.model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """
        Customize serialization to handle polymorphic nature of curves.
        """

        class SerializationHelper(pydantic.BaseModel):
            """
            An intermediate representation of market's state that is
            suitable for serialization in a way that allows to reconstruct
            the state after deserialization, with polymorphic nature of curves
            handled, and discount/index curves properly populated.
            """

            name: str
            pricing_date: Date
            instruments: Dict[str, Instrument]
            discount_curves: Dict[str, str]
            index_curves: Dict[str, str]
            index_fixings: Dict[str, List[Tuple[Date, float]]]
            all_curves: List[pydantic.SerializeAsAny[Curve]]
            all_curve_classes: List[str]  # curve types for all_curves
            spot_fx_rates: Dict[Currency, Dict[Currency, float]]

        data = SerializationHelper(
            name=self.name,
            pricing_date=self.pricing_date,
            instruments=self.instruments,
            discount_curves={k: v.get_name() for k, v in self.discount_curves.items()},
            index_curves={k: v.get_name() for k, v in self.index_curves.items()},
            index_fixings=self.index_fixings,
            all_curves=[v for _, v in self.all_curves.items()],
            all_curve_classes=[type(v).__name__ for _, v in self.all_curves.items()],
            spot_fx_rates=self.spot_fx_rates,
        )
        return data.model_dump()

    @pydantic.model_validator(mode="wrap")
    def validate_insttype(self, default_handler_func) -> Self:
        """
        Customize deserialization to handle polymorphic nature of curves.
        """
        if isinstance(self, dict) and "all_curve_classes" in self:
            data_dict = self  # self is raw dictionary in validators
            all_curves = {}
            for curve_dump, curve_class in zip(data_dict["all_curves"], data_dict["all_curve_classes"]):
                derived_cls = get_curve_class_by_name(curve_class)
                curve = derived_cls.model_validate(curve_dump)
                all_curves[curve.get_name()] = curve
            data_dict["all_curves"] = all_curves
            data_dict["discount_curves"] = {k: all_curves[v] for k, v in data_dict["discount_curves"].items()}
            data_dict["index_curves"] = {k: all_curves[v] for k, v in data_dict["index_curves"].items()}
            del data_dict["all_curve_classes"]
            fx_rates = {}
            for ccy1_str, v_raw in data_dict["spot_fx_rates"].items():
                v = {}
                for ccy2_str, fx_value in v_raw.items():
                    v[Currency(int(ccy2_str))] = fx_value
                fx_rates[Currency(int(ccy1_str))] = v
            data_dict["spot_fx_rates"] = fx_rates
        ret = default_handler_func(self)
        return ret


@dataclass
class BumpedInstrumentMarket:
    """
    Market where some instruments were bumped, and associated meta-data.
    """

    instrument: Instrument
    market: MarketView
    bump_size: float
    bump_type: int


def maybe_rebuild_curve(market: MarketView, curve: Curve) -> None:
    """
    Check if curve requires rebuilding in the context of given view,
    and rebuild by also checking and rebuilding dependencies.
    """
    if curve.is_built():
        return
    dep_curve_ids = curve.get_prerequisite_curve_ids()
    for cid in dep_curve_ids:
        depcurve = market.get_curve_by_name(cid)
        if depcurve is None:
            raise RuntimeError("Corrupted market view - curve prerequisites are missing.")
        maybe_rebuild_curve(market, depcurve)
    curve.build(market)


def get_indirect_curve_dependencies(market: MarketView, curve: Curve) -> List[str]:
    """
    Get a list of names of all curves that are prerequisite for building of the given curve.
    """
    ids = curve.get_prerequisite_curve_ids()
    for cid in ids:
        icurve = market.get_curve_by_name(cid)
        if icurve is None:
            raise RuntimeError("Corrupted market view - curve prerequisites are missing.")
        next_level_ids = get_indirect_curve_dependencies(market, icurve)
        ids.extend(next_level_ids)
    return ids


def get_indirect_curve_instruments(market: MarketView, curve: Curve) -> List[str]:
    """
    Get a list of names of all instruments that are prerequisite for building of the given curve.
    """
    instrument_ids = set()
    curves = [curve]
    for icurveid in get_indirect_curve_dependencies(market, curve):
        depcurve = market.get_curve_by_name(icurveid)
        if depcurve is None:
            raise RuntimeError("Corrupted market view - curve prerequisites are missing.")
        curves.append(depcurve)
    for icurve in curves:
        instruments = icurve.get_prerequisite_instrument_ids()
        for i in instruments:
            instrument_ids.add(i)
    return instrument_ids
