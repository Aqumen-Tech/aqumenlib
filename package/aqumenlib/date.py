# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Date class
"""

import datetime
from typing import Any, Self
from typing_extensions import Annotated
from aqumenlib.exception import AqumenException

from pydantic import BaseModel
from pydantic import ValidationError
from pydantic.functional_validators import BeforeValidator

import QuantLib as ql


class Date(BaseModel):
    """
    Date class -  represent a date.
    Internally store it as an integer that looks like ISO string, e.g. 20210517
    Provides conversions to other representations.

    When using Python typing system,
    use DateType defined below to allow implicit conversions
    in functions decorated with pydantic.validate_call
    """

    internal_isoint: int

    def year(self):
        """
        Year of this date.
        """
        return self.internal_isoint // 10000

    def month(self):
        """
        Month number of this date.
        """
        return (self.internal_isoint % 10000) // 100

    def day(self):
        """
        Day of the month number of this date.
        """
        return self.internal_isoint % 100

    def __repr__(self):
        return f"Date({self.internal_isoint})"

    def __str__(self):
        return f"{str(self.to_py())}"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Date):
            return False
        return self.internal_isoint == other.internal_isoint

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other) -> bool:
        return self.internal_isoint < other.internal_isoint

    def __le__(self, other) -> bool:
        return self.internal_isoint <= other.internal_isoint

    def __gt__(self, other) -> bool:
        return self.internal_isoint > other.internal_isoint

    def __ge__(self, other) -> bool:
        return self.internal_isoint >= other.internal_isoint

    def _advance(self, delta: int | datetime.timedelta, dir_mult: int) -> Self:
        """
        Utility used internally for addition / subtraction of days.
        Moves the date by number of days specified in delta and returns a new date.
        Direction and step can be additionally modified by
        multiplier input dir_mult (which normally would be +1 or -1).
        """
        try:
            if isinstance(delta, datetime.timedelta):
                days = delta.days * dir_mult
            else:
                days = int(delta * dir_mult)
        except (ValueError, TypeError):
            return NotImplemented
        x = self.to_excel()
        return Date.from_excel(x + days)

    def __add__(self, other) -> Self:
        return self._advance(other, +1)

    def __radd__(self, other) -> Self:
        return self._advance(other, +1)

    def __sub__(self, other) -> Self | datetime.timedelta:
        if isinstance(other, Date):
            diff = self.to_excel() - other.to_excel()
            return datetime.timedelta(days=diff)
        else:
            return self._advance(other, -1)

    def __iadd__(self, other) -> Self:
        new_dt = self._advance(other, +1)
        self.internal_isoint = new_dt.internal_isoint
        return self

    def __isub__(self, other) -> Self:
        new_dt = self._advance(other, -1)
        self.internal_isoint = new_dt.internal_isoint
        return self

    @classmethod
    def today(cls) -> Self:
        """
        Initializes the Date object from today's date.
        """
        return cls.from_py(datetime.date.today())

    @classmethod
    def from_ymd(cls, y: int, m: int, d: int) -> Self:
        """
        Initializes the Date object from year, month, day numbers.
        """
        return cls(internal_isoint=y * 10000 + m * 100 + d)

    @classmethod
    def from_py(cls, d: datetime.date) -> Self:
        """
        Initializes the Date object from a python datetime.date object
        """
        return cls(internal_isoint=d.year * 10000 + d.month * 100 + d.day)

    @classmethod
    def from_isoint(cls, v: int) -> Self:
        """
        Initializes the Date object from an integer that looks like ISO string, e.g. 20210517
        """
        return cls(internal_isoint=v)

    @classmethod
    def from_excel(cls, excel_serial) -> Self:
        """
        Initializes the Date object from an Excel serial number.
        Ignores Excel's bugs in year 1900.
        """
        return cls.from_py(excel_date_to_datetime(excel_serial))

    @classmethod
    def from_ql(cls, ql_date: ql.Date) -> Self:
        """Initializes the Date object from a QuantLib Date object"""
        v = int(ql_date.year()) * 10000 + int(ql_date.month()) * 100 + int(ql_date.dayOfMonth())
        return cls(internal_isoint=v)

    @classmethod
    def from_str(cls, v: str) -> Self:
        """Initializes the Date object from an ISO string"""
        try:
            return cls.from_py(datetime.datetime.strptime(v, "%Y-%m-%d"))
        except ValueError as exc:
            try:
                return cls.from_py(datetime.datetime.strptime(v, "%Y%m%d"))
            except ValueError:
                raise exc from exc

    @classmethod
    def from_any(cls, v: Any) -> Self:
        """
        Try to create a Date by automatically detecting input type.
        """
        if isinstance(v, Date):
            return cls(internal_isoint=v.internal_isoint)
        elif isinstance(v, datetime.date):
            return cls.from_py(v)
        elif isinstance(v, int):
            if v > 19000000 and v < 35000000:
                return cls(internal_isoint=v)
            elif v < 500_000:
                return cls.from_excel(v)
        elif isinstance(v, ql.Date):
            return cls.from_ql(v)
        elif isinstance(v, str):
            return cls.from_str(v)
        raise ValidationError(f"Could not convert to Date: {v}")

    @classmethod
    def end_of_month(cls, d: Self) -> Self:
        """
        Construct a Date object that corresponds to the last day
        in the same year and month as the provided date.
        """
        return Date.from_ql(ql.Date.endOfMonth(d.to_ql()))

    def to_py(self) -> datetime.date:
        """
        Returns the date as a python datetime.date object
        """
        year = self.internal_isoint // 10000
        month = (self.internal_isoint % 10000) // 100
        day = self.internal_isoint % 100
        return datetime.date(year, month, day)

    def to_excel(self) -> int:
        """
        Returns the date as an Excel serial number
        """
        return datetime_to_excel_date(self.to_py())

    def to_isoint(self) -> int:
        """
        Returns the date as an ISO-like integer
        """
        return self.internal_isoint

    def to_isostr(self) -> str:
        """
        Returns the date as an ISO str, e.g. 2023-08-25
        """
        year = self.internal_isoint // 10000
        month = (self.internal_isoint % 10000) // 100
        day = self.internal_isoint % 100
        return f"{year}-{month:02d}-{day:02d}"

    def to_ql(self) -> ql.Date:
        """Returns the date as a QuantLib Date object"""
        return ql.Date(self.day(), self.month(), self.year())

    def is_weekend(self) -> bool:
        """
        Return True if this date is a weekend day.
        """
        return self.to_py().weekday() >= 5


def inputconverter_date(v: Any) -> Date:
    """
    Input converter that lets pydantic accept a number of inputs for Date
    """
    return Date.from_any(v)


DateInput = Annotated[Date, BeforeValidator(inputconverter_date)]


def date_to_isoint(d: datetime.date) -> int:
    """
    represent a date as an integer that looks like ISO string, e.g. 20210517
    """
    return d.year * 10000 + d.month * 100 + d.day


def date_from_isoint(i: int) -> datetime.date:
    """
    construct a date as an integer that looks like ISO string, e.g. 20210517
    """
    y = int(i / 10000)
    m = int((i % 10000) / 100)
    d = i % 100
    return datetime.date(y, m, d)


__temp_xl_start = datetime.date(1899, 12, 30)  # intentional - not 31st Dec but 30th


def datetime_to_excel_date(dt: datetime.date) -> int:
    """
    convert datetime to Excel integer date representation
    """
    delta = dt - __temp_xl_start
    return int(delta.days)


def excel_date_to_datetime(xl_date: int) -> datetime.date:
    """
    Inverse of the above, take an Excel date (integer or float), convert it to datetime.date
    Ignores Excel's bugs in year 1900.
    """
    delta = datetime.timedelta(days=int(xl_date))
    return __temp_xl_start + delta
