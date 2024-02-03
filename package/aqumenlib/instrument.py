# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Instruments as well as its  family and type are objects used to calibrate curves and models
"""
from typing import Any, Optional, List, Self
import pydantic
import QuantLib as ql

from aqumenlib import AssetClass, RiskType, Currency
from aqumenlib.instrument_family import InstrumentFamily
from aqumenlib.instrument_type import InstrumentType, InstrumentTypeInput
from aqumenlib.state import StateManager
from aqumenlib.term import Term


class Instrument(pydantic.BaseModel):
    """
    Quoted market instrument, such as 10Y SOFR OIS, quoted at a given date.
    """

    name: str = ""
    inst_type: InstrumentType
    quote: float

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            self.name = self.inst_type.get_name()
        self._ql_relinkable_handle = ql.RelinkableQuoteHandle(ql.SimpleQuote(self.quote))

    def get_name(self) -> str:
        """
        Return ID of this object.
        """
        return self.name

    def short_str(self) -> str:
        """
        Short description of instrument, e.g. IRS-SOFR-1Y @ 0.05
        """
        return f"{self.name} @ {self.quote}"

    def get_quote(self) -> float:
        """
        Numerical quote for the instrument
        """
        return self.quote

    def set_quote(self, new_quote: float) -> float:
        """
        Change quote and relink the handle that QuantLib uses.
        """
        self.quote = new_quote
        self._ql_relinkable_handle.linkTo(ql.SimpleQuote(self.quote))

    def get_quote_hanlde(self) -> float:
        """
        QuantLib's relinkable quote handle which allows in-place modification of quotes
        without otheriwse modifying the structure of market modeling.
        """
        return self._ql_relinkable_handle

    def get_inst_type(self) -> InstrumentType:
        """
        Instrument type
        """
        return self.inst_type

    def get_inst_specifics(self) -> Any:
        """
        Instrument specifics, e.g. maturity
        """
        return self.inst_type.specifics

    def get_family(self) -> InstrumentFamily:
        """
        Instrument family
        """
        return self.inst_type.family

    def get_risk_type(self) -> RiskType:
        """
        Risk type (i.e. category) of this instrument
        """
        return self.inst_type.family.get_risk_type()

    def get_asset_class(self) -> AssetClass:
        """
        Asset class of this instrument
        """
        return self.inst_type.family.get_asset_class()

    def get_currency(self) -> Optional[Currency]:
        """
        Currency of this Instrument
        """
        return self.inst_type.family.get_currency()

    @classmethod
    def from_type(cls, inst_type: InstrumentType, quote: float) -> Self:
        """
        Make a new instrument
        """
        if isinstance(inst_type, str):
            inst_type = StateManager.get(InstrumentType, inst_type)
            if not inst_type:
                raise IndexError(f"Instrument type not found: {inst_type}")
        return Instrument(inst_type=inst_type, quote=quote)


@pydantic.validate_call
def create_instrument(
    instrument_type: InstrumentTypeInput,
    quote: float,
    name: str = "",
) -> Instrument:
    """
    Create a new instrument by combining InstrumentType object with a quote.
    """
    i = Instrument.from_type(instrument_type, quote)
    if name:
        i.name = name
    return i


def try_get_tenor_time(specifics: Any) -> Optional[float]:
    """
    If possible, try to figure out the pillar's time for an instrument.
    e.g. IRS-SONIA-5Y should have a pillar time of 5.
    """
    # TODO use pillarTime() from ql helper
    if isinstance(specifics, ql.Period):
        p = specifics
    if isinstance(specifics, Term):
        p = specifics.to_ql()
    elif isinstance(specifics, str):
        p = ql.Period(specifics)
    else:
        return None
    if p.units() == ql.Years:
        return p.length()
    elif p.units() == ql.Months:
        return p.length() / 12.0
    elif p.units() == ql.Weeks:
        return p.length() * 7 / 365.0
    elif p.units() == ql.Days:
        return p.length() / 365.0
    else:
        return None


class InstrumentFilter(pydantic.BaseModel):
    """
    Functor-like object to check if instrument matches a set of filtering criteria.
    Within each sub-filter (like currency or asset class) the check is done OR-style,
    i.e. instrument matches if it matches via any of the items in the list.
    All sub-filters are then used AND-style, i.e. instrument must match all that are provided.

    As an example, if filter currencies are USD and EUR, and risk type is RATE and RATEBASIS,
    then only rate instruments (regular and basis) within USD/EUR will be selected.
    """

    filter_instrument_name: Optional[List[str]] = None
    filter_instrument_family: Optional[List[str]] = None
    filter_currency: Optional[List[Currency]] = None
    filter_risk_type: Optional[List[RiskType]] = None
    filter_asset_class: Optional[List[AssetClass]] = None

    def matches(self, instrument: Instrument) -> bool:
        """
        Returns true if an instrument matches the filters in this object.
        """
        if self.filter_instrument_name is not None and instrument.name not in self.filter_instrument_name:
            return False
        if (
            self.filter_instrument_family is not None
            and instrument.get_family().get_name() not in self.filter_instrument_family
        ):
            return False
        if self.filter_currency is not None and instrument.get_currency() not in self.filter_currency:
            return False
        if self.filter_risk_type is not None and instrument.get_risk_type() not in self.filter_risk_type:
            return False
        if self.filter_asset_class is not None and instrument.get_asset_class() not in self.filter_asset_class:
            return False
        return True
