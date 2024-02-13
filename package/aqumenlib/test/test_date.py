# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import datetime
from aqumenlib.enums import BusinessDayAdjustment, TimeUnit
from aqumenlib.instruments.future_contract import futures_symbol_to_month_start
from pydantic import validate_call
import QuantLib as ql

from aqumenlib.date import (
    Date,
    DateInput,
    date_from_isoint,
    date_to_isoint,
    datetime_to_excel_date,
    excel_date_to_datetime,
)
from aqumenlib.calendar import Calendar, add_business_days, add_calendar_days, date_adjust, date_advance


def test_date_as_int():
    """
    Test utils.
    """
    assert date_to_isoint(datetime.date(2023, 8, 21)) == 20230821
    assert date_from_isoint(20230328) == datetime.date(2023, 3, 28)


def test_xl_date_conversion():
    """
    Test XL conversions.
    """
    assert datetime_to_excel_date(datetime.date(2023, 8, 21)) == 45_159
    assert datetime_to_excel_date(datetime.date(2003, 8, 20)) == 37_853
    assert datetime_to_excel_date(datetime.date(2053, 8, 21)) == 56_117
    # inverse
    assert excel_date_to_datetime(45_159) == datetime.date(2023, 8, 21)
    assert excel_date_to_datetime(37_853) == datetime.date(2003, 8, 20)
    assert excel_date_to_datetime(56_117) == datetime.date(2053, 8, 21)


@validate_call
def converter_func(x: DateInput) -> Date:
    """
    Converter for test.
    """
    return x


def test_date_object_create():
    """
    Test constructors.
    """
    for d in [
        Date.from_py(datetime.date(2023, 8, 21)),
        Date.from_isoint(20230821),
        Date.from_excel(45_159),
        Date.from_ql(ql.Date(21, 8, 2023)),
        Date.from_any(datetime.date(2023, 8, 21)),
        Date.from_any(20230821),
        Date.from_any(45_159),
        Date.from_any(ql.Date(21, 8, 2023)),
        Date.from_any("20230821"),
        Date.from_any("2023-08-21"),
    ]:
        assert isinstance(d, Date)
        assert d.to_isoint() == 20230821
        assert d.to_excel() == 45_159
        assert d.to_py() == datetime.date(2023, 8, 21)
        assert d.to_ql() == ql.Date(21, 8, 2023)


def test_date_converter():
    """
    Test input conversions.
    """
    for v in [datetime.date(2023, 8, 21), 20230821, 45_159]:
        d = converter_func(v)
        assert isinstance(d, Date)
        assert d.to_isoint() == 20230821
        assert d.to_excel() == 45_159
        assert d.to_py() == datetime.date(2023, 8, 21)
        assert d.to_ql() == ql.Date(21, 8, 2023)


def test_date_manipulations():
    """
    Test date add functionality.
    """
    assert add_calendar_days(Date.from_any(20231204), 7) == Date.from_isoint(20231211)
    assert add_calendar_days(Date.from_any(20231204), 10) == Date.from_isoint(20231214)
    assert add_calendar_days(Date.from_any(20231204), -7) == Date.from_isoint(20231127)
    assert add_calendar_days(Date.from_any(20231204), -10) == Date.from_isoint(20231124)
    assert add_business_days(Date.from_any(20231204), 5, ql.UnitedKingdom()) == Date.from_isoint(20231211)
    assert add_business_days(Date.from_any(20231204), 1, ql.UnitedKingdom()) == Date.from_isoint(20231205)  # Mon->Tue
    assert add_business_days(Date.from_any(20231201), 1, ql.UnitedKingdom()) == Date.from_isoint(20231204)  # Fri->Mon
    assert add_business_days(Date.from_any(20231202), 1, ql.UnitedKingdom()) == Date.from_isoint(20231204)  # Sat->Mon
    assert add_business_days(Date.from_any(20231203), 1, ql.UnitedKingdom()) == Date.from_isoint(20231204)  # Sun->Mon
    assert add_business_days(Date.from_any(20231201), 1, ql.UnitedKingdom()) == Date.from_isoint(20231204)  # Fri->Mon
    assert add_business_days(Date.from_any(20231201), 2, ql.UnitedKingdom()) == Date.from_isoint(20231205)  # Fri->Mon
    assert add_business_days(Date.from_any(20231211), -5, ql.UnitedKingdom()) == Date.from_isoint(20231204)
    assert add_business_days(Date.from_any(20231201), -1, ql.UnitedKingdom()) == Date.from_isoint(20231130)  # Fri->Thu
    assert add_business_days(Date.from_any(20231202), -1, ql.UnitedKingdom()) == Date.from_isoint(20231201)  # Sat->Fri
    assert add_business_days(Date.from_any(20231203), -1, ql.UnitedKingdom()) == Date.from_isoint(20231201)  # Sun->Fri
    assert add_business_days(Date.from_any(20231204), -1, ql.UnitedKingdom()) == Date.from_isoint(20231201)  # Mon->Fri
    assert add_business_days(Date.from_any(20231204), -2, ql.UnitedKingdom()) == Date.from_isoint(20231130)  # Mon->Thu
    assert add_business_days(Date.from_any(20231222), 1, ql.UnitedKingdom()) == Date.from_isoint(20231227)  # christmas


def test_calendar():
    """
    Test construction of calendars
    """
    t = Calendar(ql_calendar_id="TARGET")
    assert str(t.to_ql()) == "TARGET calendar"
    t = Calendar(ql_calendar_id=("UnitedKingdom", "Exchange"))
    assert str(t.to_ql()) == "London stock exchange calendar"


def test_futures_code_conversion():
    """
    Test futures code conversion to dates
    """
    assert futures_symbol_to_month_start("M25") == Date.from_ymd(2025, 6, 1)
    assert futures_symbol_to_month_start("F12") == Date.from_ymd(2012, 1, 1)
    assert futures_symbol_to_month_start("Z30") == Date.from_ymd(2030, 12, 1)


def test_dat_manipulations():
    """
    Test end of month method.
    """
    assert Date.end_of_month(Date.from_ymd(2025, 1, 15)) == Date.from_ymd(2025, 1, 31)
    assert date_advance(Date.from_ymd(2025, 12, 15), 3, TimeUnit.MONTHS) == Date.from_ymd(2026, 3, 15)
    assert date_adjust(Date.from_ymd(2024, 2, 3), ql.UnitedKingdom(), BusinessDayAdjustment.PRECEDING) == Date.from_ymd(
        2024, 2, 2
    )
