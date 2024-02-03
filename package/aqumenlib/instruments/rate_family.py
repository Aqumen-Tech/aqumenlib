# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Base class for all interest rate instruments to be used for curve calibrations.
"""
from abc import abstractmethod
from typing import Optional
import pydantic
from aqumenlib.index import Index
from aqumenlib.instrument_family import InstrumentFamily


class RateInstrumentFamily(InstrumentFamily, pydantic.BaseModel):
    """
    Base class for all interest rate instruments to be used for curve calibrations.
    """

    @abstractmethod
    def create_ql_instrument(
        self,
        market: "MarketView",
        quote_handle: "ql.RelinkableQuoteHandle",
        term: "Term",
        discounting_id: Optional[str] = None,
        target_index: Optional[Index] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
