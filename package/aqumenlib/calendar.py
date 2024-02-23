# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Calendar class - handles holidays in a given jurisdiction or location.
"""

from typing import Any, Self, Tuple
from typing_extensions import Annotated
from aqumenlib.date import Date, DateInput
from aqumenlib.enums import BusinessDayAdjustment, TimeUnit

from pydantic import BaseModel
import pydantic
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


# @pydantic.validate_call
def add_calendar_days(d: DateInput, ndays: int) -> Date:
    """
    Returns a date that is ndays calendar days away from the input date.
    """
    qd = d.to_ql()
    return Date.from_ql(qd + ndays)


# @pydantic.validate_call
def add_business_days(d: DateInput, ndays: int, calendar: Calendar | ql.Calendar) -> Date:
    """
    Returns a date that is ndays business days away from the input date.
    """
    if isinstance(calendar, Calendar):
        ql_calendar = calendar.to_ql()
    else:
        ql_calendar = calendar
    if ndays == 0:
        return d
    inc = +1 if ndays > 0 else -1
    counter = 0
    nd = d.to_ql().serialNumber()
    while counter < abs(ndays):
        nd = nd + inc
        if not ql_calendar.isHoliday(ql.Date(nd)):
            counter += 1
    return Date.from_ql(ql.Date(nd))


# @pydantic.validate_call
def date_adjust(
    d: DateInput,
    calendar: Calendar | ql.Calendar,
    adj: BusinessDayAdjustment,
) -> Self:
    """
    Adjust input date to a good business day
    """
    if isinstance(calendar, Calendar):
        ql_calendar = calendar.to_ql()
    else:
        ql_calendar = calendar
    adj_d = ql_calendar.adjust(d.to_ql(), adj.to_ql())
    return Date.from_ql(adj_d)


# @pydantic.validate_call
def date_advance(
    d: DateInput,
    n: int,
    unit: TimeUnit,
    calendar: Calendar | ql.Calendar = ql.NullCalendar(),
    adj=BusinessDayAdjustment.FOLLOWING,
    end_of_month_flag: bool = False,
) -> Date:
    """
    Returns a date that is some number of time units away from the input date.
    """
    if isinstance(calendar, Calendar):
        ql_calendar = calendar.to_ql()
    else:
        ql_calendar = calendar
    adv_d = ql_calendar.advance(d.to_ql(), n, unit.to_ql(), adj.to_ql(), end_of_month_flag)
    return Date.from_ql(adv_d)
