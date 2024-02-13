# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Term class - represents a tenor for a rate or instrument, and maps to QuantLib's Period class.
"""

from typing import Any, Optional, Self
from typing_extensions import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import BeforeValidator

import QuantLib as ql

from aqumenlib.enums import TimeUnit


class Term(BaseModel):
    """
    Term class - represents a tenor for a rate or instrument, and maps to QuantLib's Period class.
    """

    time_unit: TimeUnit
    length: int

    @classmethod
    def from_str(cls, s: str) -> Self:
        """
        Initializes the Term object from a string like 3M or 10Y
        """
        p = ql.Period(s)
        return Term.from_ql(p)

    @classmethod
    def from_ql(cls, p: str) -> Self:
        """
        Initializes the Term object from QuantLib Period object.
        """
        return Term(time_unit=TimeUnit(p.units()), length=p.length())

    def to_ql(self) -> ql.Period:
        """
        Convert to QuantLib Period.
        """
        return ql.Period(self.length, self.time_unit.value)

    def __str__(self) -> str:
        return str(self.to_ql())


def inputconverter_term(v: Any) -> Term:
    """
    Input converter that lets pydantic accept a number of inputs for Term
    """
    if isinstance(v, Term):
        return v
    if isinstance(v, ql.Period):
        return Term.from_ql(v)
    if isinstance(v, str):
        return Term.from_str(v)


TermInput = Annotated[Term, BeforeValidator(inputconverter_term)]


class Tenors:
    """
    Enum-like class for convenience of picking standard tenos for instruments.
    """

    OneDay = Term(time_unit=TimeUnit.DAYS, length=1)
    TwoDays = Term(time_unit=TimeUnit.DAYS, length=2)
    ThreeDays = Term(time_unit=TimeUnit.DAYS, length=3)
    OneWeek = Term(time_unit=TimeUnit.WEEKS, length=1)
    TwoWeeks = Term(time_unit=TimeUnit.WEEKS, length=2)
    ThreeWeeks = Term(time_unit=TimeUnit.WEEKS, length=3)
    FourWeeks = Term(time_unit=TimeUnit.WEEKS, length=4)
    OneMonth = Term(time_unit=TimeUnit.MONTHS, length=1)
    TwoMonths = Term(time_unit=TimeUnit.MONTHS, length=2)
    ThreeMonths = Term(time_unit=TimeUnit.MONTHS, length=3)
    FourMonths = Term(time_unit=TimeUnit.MONTHS, length=4)
    FiveMonths = Term(time_unit=TimeUnit.MONTHS, length=5)
    SixMonths = Term(time_unit=TimeUnit.MONTHS, length=6)
    SevenMonths = Term(time_unit=TimeUnit.MONTHS, length=7)
    EightMonths = Term(time_unit=TimeUnit.MONTHS, length=8)
    NineMonths = Term(time_unit=TimeUnit.MONTHS, length=9)
    TenMonths = Term(time_unit=TimeUnit.MONTHS, length=10)
    ElevenMonths = Term(time_unit=TimeUnit.MONTHS, length=11)
    TwelveMonths = Term(time_unit=TimeUnit.MONTHS, length=12)
    ThirteenMonths = Term(time_unit=TimeUnit.MONTHS, length=13)
    FourteenMonths = Term(time_unit=TimeUnit.MONTHS, length=14)
    FifteenMonths = Term(time_unit=TimeUnit.MONTHS, length=15)
    SixteenMonths = Term(time_unit=TimeUnit.MONTHS, length=16)
    SeventeenMonths = Term(time_unit=TimeUnit.MONTHS, length=17)
    EighteenMonths = Term(time_unit=TimeUnit.MONTHS, length=18)
    OneYear = Term(time_unit=TimeUnit.YEARS, length=1)
    TwoYears = Term(time_unit=TimeUnit.YEARS, length=2)
    ThreeYears = Term(time_unit=TimeUnit.YEARS, length=3)
    FourYears = Term(time_unit=TimeUnit.YEARS, length=4)
    FiveYears = Term(time_unit=TimeUnit.YEARS, length=5)
    SixYears = Term(time_unit=TimeUnit.YEARS, length=6)
    SevenYears = Term(time_unit=TimeUnit.YEARS, length=7)
    EightYears = Term(time_unit=TimeUnit.YEARS, length=8)
    NineYears = Term(time_unit=TimeUnit.YEARS, length=9)
    TenYears = Term(time_unit=TimeUnit.YEARS, length=10)
    ElevenYears = Term(time_unit=TimeUnit.YEARS, length=11)
    TwelveYears = Term(time_unit=TimeUnit.YEARS, length=12)
    ThirteenYears = Term(time_unit=TimeUnit.YEARS, length=13)
    FourteenYears = Term(time_unit=TimeUnit.YEARS, length=14)
    FifteenYears = Term(time_unit=TimeUnit.YEARS, length=15)
    SixteenYears = Term(time_unit=TimeUnit.YEARS, length=16)
    SeventeenYears = Term(time_unit=TimeUnit.YEARS, length=17)
    EighteenYears = Term(time_unit=TimeUnit.YEARS, length=18)
    NineteenYears = Term(time_unit=TimeUnit.YEARS, length=19)
    TwentyYears = Term(time_unit=TimeUnit.YEARS, length=20)
    TwentyFiveYears = Term(time_unit=TimeUnit.YEARS, length=25)
    ThirtyYears = Term(time_unit=TimeUnit.YEARS, length=30)
    ThirtyFiveYears = Term(time_unit=TimeUnit.YEARS, length=35)
    FourtyYears = Term(time_unit=TimeUnit.YEARS, length=40)
    FourtyFiveYears = Term(time_unit=TimeUnit.YEARS, length=45)
    FiftyYears = Term(time_unit=TimeUnit.YEARS, length=50)

    D1 = Term(time_unit=TimeUnit.DAYS, length=1)
    D2 = Term(time_unit=TimeUnit.DAYS, length=2)
    D3 = Term(time_unit=TimeUnit.DAYS, length=3)
    W1 = Term(time_unit=TimeUnit.WEEKS, length=1)
    W2 = Term(time_unit=TimeUnit.WEEKS, length=2)
    W3 = Term(time_unit=TimeUnit.WEEKS, length=3)
    W4 = Term(time_unit=TimeUnit.WEEKS, length=4)
    M1 = Term(time_unit=TimeUnit.MONTHS, length=1)
    M2 = Term(time_unit=TimeUnit.MONTHS, length=2)
    M3 = Term(time_unit=TimeUnit.MONTHS, length=3)
    M4 = Term(time_unit=TimeUnit.MONTHS, length=4)
    M5 = Term(time_unit=TimeUnit.MONTHS, length=5)
    M6 = Term(time_unit=TimeUnit.MONTHS, length=6)
    M7 = Term(time_unit=TimeUnit.MONTHS, length=7)
    M8 = Term(time_unit=TimeUnit.MONTHS, length=8)
    M9 = Term(time_unit=TimeUnit.MONTHS, length=9)
    M10 = Term(time_unit=TimeUnit.MONTHS, length=10)
    M11 = Term(time_unit=TimeUnit.MONTHS, length=11)
    M12 = Term(time_unit=TimeUnit.MONTHS, length=12)
    M13 = Term(time_unit=TimeUnit.MONTHS, length=13)
    M14 = Term(time_unit=TimeUnit.MONTHS, length=14)
    M15 = Term(time_unit=TimeUnit.MONTHS, length=15)
    M16 = Term(time_unit=TimeUnit.MONTHS, length=16)
    M17 = Term(time_unit=TimeUnit.MONTHS, length=17)
    M18 = Term(time_unit=TimeUnit.MONTHS, length=18)
    Y1 = Term(time_unit=TimeUnit.YEARS, length=1)
    Y2 = Term(time_unit=TimeUnit.YEARS, length=2)
    Y3 = Term(time_unit=TimeUnit.YEARS, length=3)
    Y4 = Term(time_unit=TimeUnit.YEARS, length=4)
    Y5 = Term(time_unit=TimeUnit.YEARS, length=5)
    Y6 = Term(time_unit=TimeUnit.YEARS, length=6)
    Y7 = Term(time_unit=TimeUnit.YEARS, length=7)
    Y8 = Term(time_unit=TimeUnit.YEARS, length=8)
    Y9 = Term(time_unit=TimeUnit.YEARS, length=9)
    Y10 = Term(time_unit=TimeUnit.YEARS, length=10)
    Y11 = Term(time_unit=TimeUnit.YEARS, length=11)
    Y12 = Term(time_unit=TimeUnit.YEARS, length=12)
    Y13 = Term(time_unit=TimeUnit.YEARS, length=13)
    Y14 = Term(time_unit=TimeUnit.YEARS, length=14)
    Y15 = Term(time_unit=TimeUnit.YEARS, length=15)
    Y16 = Term(time_unit=TimeUnit.YEARS, length=16)
    Y17 = Term(time_unit=TimeUnit.YEARS, length=17)
    Y18 = Term(time_unit=TimeUnit.YEARS, length=18)
    Y19 = Term(time_unit=TimeUnit.YEARS, length=19)
    Y20 = Term(time_unit=TimeUnit.YEARS, length=20)
    Y25 = Term(time_unit=TimeUnit.YEARS, length=25)
    Y30 = Term(time_unit=TimeUnit.YEARS, length=30)
    Y35 = Term(time_unit=TimeUnit.YEARS, length=35)
    Y40 = Term(time_unit=TimeUnit.YEARS, length=40)
    Y45 = Term(time_unit=TimeUnit.YEARS, length=45)
    Y50 = Term(time_unit=TimeUnit.YEARS, length=50)
