# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024
"""
Pre-defined indices
"""
import QuantLib as ql
from aqumenlib.enums import TimeUnit
from aqumenlib.enums import Frequency
from aqumenlib.currency import Currency
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.index import RateIndex, InflationIndex
from aqumenlib.term import Term

#
# overnight indices
#

AONIA = RateIndex(
    name="AONIA",
    description="Australia Overnight Index Average",
    is_builtin=True,
    currency=Currency.AUD,
    tenor=Term.from_str("1D"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="Australia"),
    day_count=DayCount.ACT365F,
)
CORRA = RateIndex(
    name="CORRA",
    description="Canadian Overnight Repo Rate Average",
    is_builtin=True,
    currency=Currency.CAD,
    tenor=Term.from_str("1D"),
    days_to_settle=1,
    calendar=Calendar(ql_calendar_id="Canada"),
    day_count=DayCount.ACT365F,
)
ESTR = RateIndex(
    name="ESTR",
    description="Euro Short Term Rate",
    is_builtin=True,
    currency=Currency.EUR,
    tenor=Term.from_str("1D"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="TARGET"),
    day_count=DayCount.ACT360,
)
FEDFUNDS = RateIndex(
    name="FEDFUNDS",
    description="Federal Reserve Target Rate",
    is_builtin=True,
    currency=Currency.USD,
    tenor=Term.from_str("1D"),
    days_to_settle=1,
    calendar=Calendar(ql_calendar_id=("UnitedStates", "SOFR")),
    day_count=DayCount.ACT360,
)
SARON = RateIndex(
    name="SARON",
    description="Swiss Average Rate Overnight",
    is_builtin=True,
    currency=Currency.CHF,
    tenor=Term.from_str("1D"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="Switzerland"),
    day_count=DayCount.ACT360,
)
SOFR = RateIndex(
    name="SOFR",
    description="Secured Overnight Financing Rate",
    is_builtin=True,
    currency=Currency.USD,
    tenor=Term.from_str("1D"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id=("UnitedStates", "SOFR")),
    day_count=DayCount.ACT360,
)
SONIA = RateIndex(
    name="SONIA",
    description="Sterling Overnight Index Average",
    is_builtin=True,
    currency=Currency.GBP,
    tenor=Term.from_str("1D"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="UnitedKingdom"),
    day_count=DayCount.ACT365F,
)
TONAR = RateIndex(
    name="TONAR",
    description="Tokyo Overnight Average Rate",
    is_builtin=True,
    currency=Currency.JPY,
    tenor=Term.from_str("1D"),
    days_to_settle=1,
    calendar=Calendar(ql_calendar_id="Japan"),
    day_count=DayCount.ACT365F,
)

#
# term indices
#

BBSW3M = RateIndex(
    name="BBSW3M",
    description="Australia Bank Bill Swap Rate",
    is_builtin=True,
    currency=Currency.AUD,
    tenor=Term.from_str("3M"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="Australia"),
    day_count=DayCount.ACT365F,
)
BBSW6M = RateIndex(
    name="BBSW6M",
    description="Australia Bank Bill Swap Rate",
    is_builtin=True,
    currency=Currency.AUD,
    tenor=Term.from_str("6M"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="Australia"),
    day_count=DayCount.ACT365F,
)
BKBM3M = RateIndex(
    name="BKBM3M",
    description="New Zealand Bank Bill Reference Rates",
    is_builtin=True,
    currency=Currency.NZD,
    tenor=Term.from_str("3M"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="NewZealand"),
    day_count=DayCount.ACT365F,
)
BUBOR6M = RateIndex(
    name="BUBOR6M",
    description="Bucharest Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.HUF,
    tenor=Term.from_str("6M"),
    days_to_settle=2,
    calendar=Calendar(ql_calendar_id="TARGET"),
    day_count=DayCount.ACT360,
)
CIBOR6M = RateIndex(
    name="CIBOR6M",
    description="Copehagen Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.DKK,
    tenor=Term.from_str("6M"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="Denmark"),
    day_count=DayCount.ACT360,
)
euribor_rates = {}
for tenor in [1, 3, 6, 12]:
    euribor_rates[tenor] = RateIndex(
        name=f"EURIBOR{tenor}M",
        description="Europe Interbank Offered Rate",
        is_builtin=True,
        currency=Currency.EUR,
        tenor=Term(time_unit=TimeUnit.MONTHS, length=tenor),
        days_to_settle=2,
        calendar=Calendar(ql_calendar_id="TARGET"),
        day_count=DayCount.ACT360,
    )
EURIBOR1M = euribor_rates[1]
EURIBOR3M = euribor_rates[3]
EURIBOR6M = euribor_rates[6]
EURIBOR12M = euribor_rates[12]
HIBOR3M = RateIndex(
    name="HIBOR3M",
    description="Hong Gong Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.HKD,
    tenor=Term.from_str("3M"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="HongKong"),
    day_count=DayCount.ACT365F,
)
JIBAR3M = RateIndex(
    name="JIBAR3M",
    description="Johannesburg Interbank Agreed Rate",
    is_builtin=True,
    currency=Currency.ZAR,
    tenor=Term.from_str("3M"),
    days_to_settle=0,
    calendar=Calendar(ql_calendar_id="SouthAfrica"),
    day_count=DayCount.ACT365F,
)
NIBOR6M = RateIndex(
    name="NIBOR6M",
    description="Norwegian Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.NOK,
    tenor=Term.from_str("6M"),
    days_to_settle=2,
    calendar=Calendar(ql_calendar_id="Norway"),
    day_count=DayCount.ACT360,
)
PRIBOR6M = RateIndex(
    name="PRIBOR6M",
    description="Prague Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.CZK,
    tenor=Term.from_str("6M"),
    days_to_settle=2,
    calendar=Calendar(ql_calendar_id="CzechRepublic"),
    day_count=DayCount.ACT360,
)
STIBOR3M = RateIndex(
    name="STIBOR3M",
    description="Stockholm Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.SEK,
    tenor=Term.from_str("3M"),
    days_to_settle=2,
    calendar=Calendar(ql_calendar_id="Sweden"),
    day_count=DayCount.ACT360,
)
TIIE28D = RateIndex(
    name="TIIE28D",
    description="Mexico Tasa de interés interbancaria de equilibrio (Interbank Equilibrium Interest Rate)",
    is_builtin=True,
    currency=Currency.MXN,
    tenor=Term(time_unit=TimeUnit.DAYS, length=28),
    days_to_settle=1,
    calendar=Calendar(ql_calendar_id="Mexico"),
    day_count=DayCount.ACT360,
)
WIBOR6M = RateIndex(
    name="WIBOR6M",
    description="Warsaw Interbank Offered Rate",
    is_builtin=True,
    currency=Currency.PLN,
    tenor=Term.from_str("6M"),
    days_to_settle=2,
    calendar=Calendar(ql_calendar_id="Poland"),
    day_count=DayCount.ACT365F,
)

##
## inflation indices
##

UKRPI = InflationIndex(
    name="UKRPI",
    description="UK RPI inflation index",
    currency=Currency.GBP,
    ql_index=ql.UKRPI(),
)
UKHICP = InflationIndex(
    name="UKHICP",
    description="UK HICP inflation index",
    currency=Currency.GBP,
    ql_index=ql.UKHICP(),
)
USCPI = InflationIndex(
    name="USCPI",
    description="US CPI inflation index",
    currency=Currency.USD,
    ql_index=ql.USCPI(),
)
AUCPI = InflationIndex(
    name="AUCPI",
    description="Australia CPI inflation index",
    currency=Currency.AUD,
    ql_index=ql.AUCPI(Frequency.QUARTERLY.value, False),
)
ZACPI = InflationIndex(
    name="ZACPI",
    description="South Africa CPI inflation index",
    currency=Currency.ZAR,
    ql_index=ql.ZACPI(),
)
FRHICP = InflationIndex(
    name="FRHICP",
    description="France HICP inflation index",
    currency=Currency.EUR,
    ql_index=ql.FRHICP(),
)
EUHICP = InflationIndex(
    name="EUHICP",
    description="EU HICP inflation index",
    currency=Currency.EUR,
    ql_index=ql.EUHICP(),
)
