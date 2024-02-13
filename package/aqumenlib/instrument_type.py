# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Class InstrumentType - type of an instrument, such as 10Y SOFR OIS.
Also related functionality.
"""
from typing import Any, Self
from typing_extensions import Annotated
import pydantic
from pydantic.functional_validators import BeforeValidator

from aqumenlib import AssetClass, Currency, RiskType
from aqumenlib.instrument_family import (
    InstrumentFamily,
    get_instrument_family_class_by_name,
    inputconverter_inst_family,
)
from aqumenlib.namedobject import NamedObject
from aqumenlib.state import StateManager
from aqumenlib.term import Term, inputconverter_term


class InstrumentType(NamedObject, pydantic.BaseModel):
    """
    Type of an instrument, such as 10Y SOFR OIS,
    which can form an instrument by quoting it on a particular day
    """

    name: str = ""
    family: pydantic.SerializeAsAny[InstrumentFamily]
    specifics: Term | str  # TODO this requires class hierarchy
    family_class: str = ""  # internal, descriminator for de-serialization

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            self.name = f"{self.family.get_name()}-{self.specifics}"
        self.family_class = type(self.family).__name__

    @pydantic.model_validator(mode="wrap")
    def validate_insttype(self, default_handler_func) -> Self:
        """
        Customize deserialization to handle polymorphic nature of instrument family field.
        """
        if isinstance(self, dict) and isinstance(self["family"], dict):
            data_dict = self  # self is raw dictionary in validators
            derived_cls = get_instrument_family_class_by_name(data_dict["family_class"])
            data_dict["family"] = derived_cls.model_validate(data_dict["family"])
            return default_handler_func(data_dict)
        return default_handler_func(self)

    def get_name(self) -> str:
        """
        Return ID of this object.
        """
        return self.name

    def get_currency(self) -> Currency:
        """
        Currency of the instrument
        """
        return self.family.get_currency()

    def get_risk_type(self) -> RiskType:
        """
        Risk type (i.e. category) of this instrument
        """
        return self.family.get_risk_type()

    def get_asset_class(self) -> AssetClass:
        """
        Asset class of this instrument
        """
        return self.family.get_asset_class()


def inputconverter_inst_type(v: Any) -> InstrumentType:
    """
    Input converter that lets pydantic accept a number of inputs for InstrumentType
    """
    if isinstance(v, InstrumentType):
        return v
    elif isinstance(v, str):
        return StateManager.get(InstrumentType, v)
    elif isinstance(v, tuple):
        fam = inputconverter_inst_family(v[0])
        specifics = fam.specifics_input_process(v[1])
        return InstrumentType(family=fam, specifics=specifics)
    else:
        raise pydantic.ValidationError(f"Could not convert input to InstrumentType: {v}")


InstrumentTypeInput = Annotated[InstrumentType, BeforeValidator(inputconverter_inst_type)]
