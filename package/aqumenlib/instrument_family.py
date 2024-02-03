# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
InstrumentFamily class that represents broad families of instrument, e.g. SOFR OIS.
Also related functionality such as input converters.
"""

from abc import abstractmethod
from typing import Any, List, Optional, Dict

import pydantic
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from aqumenlib.state import StateManager
from aqumenlib import AssetClass, Currency, RiskType
from aqumenlib.index import Index
from aqumenlib.namedobject import NamedObject


class InstrumentFamilyMeta(pydantic.BaseModel):
    """
    Meta-data used for classification of instruments.
    Each most derived instrument family class will create an instance of this
    """

    currency: Currency
    currency2: Optional[Currency] = None
    risk_type: RiskType
    asset_class: AssetClass


_subclass_registry_instrument_family: Dict[str, type] = {}


def get_instrument_family_class_by_name(family_class_name: str) -> type:
    """
    Find a class of derived instrument family - useful in serialization etc.
    """
    return _subclass_registry_instrument_family[family_class_name]


class InstrumentFamily(NamedObject, pydantic.BaseModel):
    """
    Family of instrument types, such as SOFR OIS.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _subclass_registry_instrument_family[cls.__name__] = cls

    @abstractmethod
    def get_meta(self) -> InstrumentFamilyMeta:
        """
        The meta-data for this instrument family, like it's risk type
        """

    @abstractmethod
    def get_underlying_indices(self) -> List[Index]:
        """
        List of indices on each the instruments in this family depend.
        """

    def get_default_bump(self) -> float:
        """
        Default value of the bump to use for the instruments in this family
        when performing sensitivity calculations.
        This should be overridden in derived classes as needed.
        """
        return 0.0001

    def bump_quote(self, old_quote: float, bump_size: float) -> float:
        """
        Calculate new quote given a bump that should apply to a relevant underlying metric.
        For example, if the instrument is a rate futures one where quote is presented as 100*(1-r)
        where r is underlying rate, then this method will be overwritten in
        the most derived instrument family to return q - bump_size*100
        """
        return old_quote + bump_size

    def get_currency(self) -> Optional[Currency]:
        """
        Currency of the instrument
        """
        return self.get_meta().currency

    def get_risk_type(self) -> RiskType:
        """
        Risk type (i.e. category) of this instrument
        """
        return self.get_meta().risk_type

    def get_asset_class(self) -> AssetClass:
        """
        Asset class of this instrument
        """
        return self.get_meta().asset_class


def inputconverter_inst_family(v: Any) -> InstrumentFamily:
    """
    Input converter that lets pydantic accept a number of inputs for InstrumentType
    """
    if isinstance(v, InstrumentFamily):
        return v
    elif isinstance(v, str):
        return StateManager.get(InstrumentFamily, v)
    else:
        raise pydantic.ValidationError(f"Could not convert input to InstrumentFamily: {v}")


InstrumentFamilyInput = Annotated[InstrumentFamily, BeforeValidator(inputconverter_inst_family)]
