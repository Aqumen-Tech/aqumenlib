# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Day count functionality.
"""

from enum import Enum, unique

import QuantLib as ql


@unique
class DayCount(Enum):
    """
    Day count conventions supported by the library.
    """

    ACT360 = 1
    ACT366 = 2
    ACT364 = 3
    BUS252 = 4
    ACT365F = 10
    ACT365F_CANADIAN = 11  # aka CAD/365
    ACT365F_NOLEAP = 12  # aka NL/365
    ACT365_25 = 15  # aka Act/365.25

    ACTACT_ISMA = 20  # aka Act/Act ICMA, ISMA-99
    ACTACT_ISDA = 21  # aka Act/365
    ACTACT_BOND = 22
    ACTACT_HISTORICAL = 23
    ACTACT_365 = 24
    ACTACT_AFB = 25
    ACTACT_EURO = 26

    THIRTY365 = 30  # aka 30E/365 aka 30E/Act German
    THIRTY360_USA = 31
    THIRTY360_BONDBASIS = 32
    THIRTY360_EUROPEAN = 33
    THIRTY360_EUROBONDBASIS = 34
    THIRTY360_ITALIAN = 35
    THIRTY360_GERMAN = 36
    THIRTY360_ISMA = 37
    THIRTY360_ISDA = 38
    THIRTY360_NASD = 39

    def to_ql(self) -> ql.DayCounter:
        """
        Get an equivalent QuantLib DayCounter object.
        Example usage: DayCount.ACT365_25.to_ql()
        """
        global _ql_daycount_map
        return _ql_daycount_map[self]


_ql_daycount_map = {
    DayCount.ACT360: ql.Actual360(),
    DayCount.ACT366: ql.Actual366(),
    DayCount.ACT364: ql.Actual364(),
    DayCount.BUS252: ql.Business252(),
    DayCount.ACT365F: ql.Actual365Fixed(ql.Actual365Fixed.Standard),
    DayCount.ACT365F_CANADIAN: ql.Actual365Fixed(ql.Actual365Fixed.Canadian),
    DayCount.ACT365F_NOLEAP: ql.Actual365Fixed(ql.Actual365Fixed.NoLeap),
    DayCount.ACT365_25: ql.Actual36525(),
    DayCount.ACTACT_ISMA: ql.ActualActual(ql.ActualActual.ISMA),
    DayCount.ACTACT_ISDA: ql.ActualActual(ql.ActualActual.ISDA),
    DayCount.ACTACT_BOND: ql.ActualActual(ql.ActualActual.Bond),
    DayCount.ACTACT_HISTORICAL: ql.ActualActual(ql.ActualActual.Historical),
    DayCount.ACTACT_365: ql.ActualActual(ql.ActualActual.Actual365),
    DayCount.ACTACT_AFB: ql.ActualActual(ql.ActualActual.AFB),
    DayCount.ACTACT_EURO: ql.ActualActual(ql.ActualActual.Euro),
    DayCount.THIRTY365: ql.Thirty365(),
    DayCount.THIRTY360_USA: ql.Thirty360(ql.Thirty360.USA),
    DayCount.THIRTY360_BONDBASIS: ql.Thirty360(ql.Thirty360.BondBasis),
    DayCount.THIRTY360_EUROPEAN: ql.Thirty360(ql.Thirty360.European),
    DayCount.THIRTY360_EUROBONDBASIS: ql.Thirty360(ql.Thirty360.EurobondBasis),
    DayCount.THIRTY360_ITALIAN: ql.Thirty360(ql.Thirty360.Italian),
    DayCount.THIRTY360_GERMAN: ql.Thirty360(ql.Thirty360.German),
    DayCount.THIRTY360_ISMA: ql.Thirty360(ql.Thirty360.ISMA),
    DayCount.THIRTY360_ISDA: ql.Thirty360(ql.Thirty360.ISDA),
    DayCount.THIRTY360_NASD: ql.Thirty360(ql.Thirty360.NASD),
}
