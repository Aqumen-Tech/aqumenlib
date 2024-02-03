# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Calendar class - handles holidays in a given jurisdiction or location.
"""

from typing import Any, Self, Tuple
from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

import QuantLib as ql

from aqumenlib.exception import AqumenException


class Calendar(BaseModel):
    """
    Calendar class - handles holidays in a given jurisdiction or location.
    Can be generated either by refering to a predefined QuantLib calendar, by
    setting ql_calendar_id to either a string (e.g. TARGET) or a tuple of string,
     = _QuantLib.UnitedKingdom_Exchange
    e.g. ("UnitedKingdom", "Exchange") will use ql.UnitedKingdom(ql.UnitedKingdom.Exchange).

    Calendars can also be loaded dynamically from files, in which cases loaded_calendar_id
    should be set to file's name without path or extension.

    If both are set, the calendar will be using holidays from both QuantLib's implementation and
    the loaded set of dates.
    """

    ql_calendar_id: str | Tuple[str, str] = ""
    loaded_calendar_id: str = ""

    def model_post_init(self, __context):
        self._ql_calendar = None
        if not self.ql_calendar_id and not self.loaded_calendar_id:
            self._ql_calendar = ql.NullCalendar()
        if self.loaded_calendar_id:
            raise NotImplementedError("Dynamic loading of calendars is not implemented yet")
        if self.ql_calendar_id:
            if isinstance(self.ql_calendar_id, str):
                if not hasattr(ql, self.ql_calendar_id):
                    raise AqumenException(f"QuantLib does not have calendar with id {(ql, self.ql_calendar_id)}")
                self._ql_calendar = getattr(ql, self.ql_calendar_id)()
            if isinstance(self.ql_calendar_id, tuple):
                id1 = self.ql_calendar_id[0]
                id2 = self.ql_calendar_id[1]
                if not hasattr(ql, id1):
                    raise AqumenException(f"QuantLib does not have calendar with id {(ql, id1)}")
                cal1 = getattr(ql, id1)
                if not hasattr(cal1, id2):
                    raise AqumenException(f"QuantLib calendars for {id1} does not have include {id2}")
                cal2 = getattr(cal1, id2)
                self._ql_calendar = cal1(cal2)
        if self._ql_calendar is None:
            raise AqumenException(f"Internal error initializing calendar: {self}")

    def to_ql(self):
        """
        Convert to QuantLib Calendar.
        """
        return self._ql_calendar


def inputconverter_calendar(v: Any) -> Calendar:
    """
    Input converter that lets pydantic accept a number of inputs for Term
    """
    if isinstance(v, Calendar):
        return v
    if isinstance(v, str) or isinstance(v, tuple):
        return Calendar(ql_calendar_id=v)


CalendarInput = Annotated[Calendar, BeforeValidator(inputconverter_calendar)]
