# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Index classes
"""
from abc import abstractmethod
from typing import Any, Optional
import pydantic

import QuantLib as ql
from aqumenlib.daycount import DayCount
from aqumenlib.currency import Currency
from aqumenlib.enums import BusinessDayAdjustment, TimeUnit
from aqumenlib.term import Term
from aqumenlib.calendar import Calendar
from aqumenlib.namedobject import NamedObject


class Index(NamedObject):
    """
    Any observable index
    """

    @abstractmethod
    def get_ql_index(self) -> ql.Index:
        """
        QuantLib representation of this index.
        """

    @abstractmethod
    def get_currency(self) -> Optional[Currency]:
        """
        Currency of the index, if applicable.
        """


class RateIndex(Index, pydantic.BaseModel):
    """
    Interest rate index like SOFR, SONIA or USLIBOR
    """

    name: str
    description: str
    is_builtin: bool = True
    currency: Currency
    tenor: Term
    days_to_settle: int
    calendar: Calendar
    day_count: DayCount
    bd_convention: BusinessDayAdjustment = BusinessDayAdjustment.MODIFIEDFOLLOWING
    end_of_month: bool = False

    def model_post_init(self, __context):
        self._ql_index = None

    def get_currency(self):
        return self.currency

    def get_name(self):
        return self.name

    def is_overnight(self) -> bool:
        """
        Returns True if this is an Overnight Index like SOFR or SONIA
        """
        return self.tenor.time_unit == TimeUnit.DAYS and self.tenor.length == 1

    def get_ql_index(self) -> ql.IborIndex:
        """
        QuantLib representation of this index
        """
        if self._ql_index:
            return self._ql_index
        if self.is_overnight():
            self._ql_index = ql.OvernightIndex(
                self.name,
                self.days_to_settle,
                self.currency.to_ql(),
                self.calendar.to_ql(),
                self.day_count.to_ql(),
            )
        else:
            self._ql_index = ql.IborIndex(
                self.name,
                self.tenor.to_ql(),
                self.days_to_settle,
                self.currency.to_ql(),
                self.calendar.to_ql(),
                self.bd_convention.to_ql(),
                self.end_of_month,
                self.day_count.to_ql(),
            )
        return self._ql_index


class InflationIndex(Index, pydantic.BaseModel):
    """
    Price-like inflation index - e.g. UK RPI
    """

    name: str
    description: str
    is_builtin: bool = True
    currency: Currency
    ql_index: Any

    def get_currency(self):
        return self.currency

    def get_name(self):
        return self.name

    def get_ql_index(self) -> ql.ZeroInflationIndex:
        return self.ql_index
