# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Base interface for all curves
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pydantic
import QuantLib as ql

_subclass_registry_curve: Dict[str, type] = {}


def get_curve_class_by_name(curve_class_name: str) -> type:
    """
    Find a class of derived Curve - useful in serialization etc.
    """
    return _subclass_registry_curve[curve_class_name]


class Curve(ABC, pydantic.BaseModel):
    """
    A base class for all curves. Curves are fundamental to market modeling
    and represent a relationship between time and some value
    (in other words, each curve is a one dimensional function of time).

    Curve objects should only have string ID based relationships to other
    curves and underlying instruments. That allows curves to be added
    to any MarketView object that satisfies these dependencies.
    Only by calling build() does the curve produce artefacts that
    bind it to actual Instrument objects and create QuantLib curves.
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        _subclass_registry_curve[cls.__name__] = cls

    @abstractmethod
    def get_name(self) -> str:
        """
        ID of the curve - this must be set as it will be used
        for dependency tracking.
        """

    @abstractmethod
    def get_ql_curve(self) -> ql.TermStructure:
        """
        QuantLib curve object for this curve (not QuantLib handle, just the term structure)
        """

    @abstractmethod
    def build(self, market: "MarketView") -> None:
        """
        Perform calibration of this curve. This should not be called by the users
        directly.
        """

    @abstractmethod
    def is_built(self) -> bool:
        """
        Check if this curve has been calibrated.
        """

    @abstractmethod
    def reset(self):
        """
        Remove all internal configuration specific to a particular market view.
        """

    @abstractmethod
    def get_prerequisite_instrument_ids(self) -> List[str]:
        """
        Return a list of identifiers of instruments that this curve depends on.
        """

    @abstractmethod
    def get_prerequisite_curve_ids(self) -> List[str]:
        """
        Return a list of identifiers of curves that this curve depends on.
        """
