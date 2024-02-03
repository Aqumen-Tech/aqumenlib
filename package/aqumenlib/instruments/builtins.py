# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Module where pre-built instruments are defined and added to state manager
"""

from collections import namedtuple
import QuantLib as ql

from aqumenlib import Currency, Frequency
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.instrument_family import InstrumentFamily
from aqumenlib.instruments.irbasis_family import IRBasisSwapFamily
from aqumenlib.state import StateManager
from aqumenlib.index import Index
from aqumenlib import indices
from aqumenlib.instruments.irs_family import IRSwapFamily
from aqumenlib.instruments.zero_coupon import ZeroCouponBondFamily
from aqumenlib.instruments.cash_family import CashDepoFamily
from aqumenlib.instrument_type import InstrumentType
from aqumenlib.bond_type import BondType
from aqumenlib.term import Term

for member in dir(indices):
    if isinstance(member, Index):
        StateManager.store(Index, member)


ois_families = [
    IRSwapFamily(name="IRS-AONIA", index=indices.AONIA, settlement_delay=2),
    IRSwapFamily(name="IRS-CORRA", index=indices.CORRA, settlement_delay=1),
    IRSwapFamily(name="IRS-FEDFUNDS", index=indices.FEDFUNDS, settlement_delay=1),
    IRSwapFamily(name="IRS-ESTR", index=indices.ESTR, settlement_delay=1),
    IRSwapFamily(name="IRS-SARON", index=indices.SARON, settlement_delay=2),
    IRSwapFamily(name="IRS-SOFR", index=indices.SOFR, settlement_delay=2),
    IRSwapFamily(name="IRS-SONIA", index=indices.SONIA, settlement_delay=1),
    IRSwapFamily(name="IRS-TONAR", index=indices.TONAR, settlement_delay=2),
]

ois_tenors = (
    [ql.Period(m, ql.Days) for m in range(1, 7)]
    + [ql.Period(m, ql.Weeks) for m in range(1, 5)]
    + [ql.Period(m, ql.Months) for m in range(1, 23)]
    + [ql.Period(y, ql.Years) for y in range(1, 31)]
)
swap_tenors = [ql.Period(m, ql.Months) for m in range(1, 13)] + [ql.Period(y, ql.Years) for y in range(1, 31)]
zc_bond_tenors = swap_tenors
cash_tenors = (
    [ql.Period(m, ql.Days) for m in range(1, 3)]
    + [ql.Period(m, ql.Weeks) for m in range(1, 5)]
    + [ql.Period(m, ql.Months) for m in range(1, 13)]
    + [ql.Period(m, ql.Years) for m in [1]]
)


for swap_family in ois_families:
    StateManager.store(InstrumentFamily, swap_family)
    for term in ois_tenors:
        i = InstrumentType(family=swap_family, specifics=Term.from_ql(term))
        StateManager.store(InstrumentType, i)


IRSConventions = namedtuple("IRSConventions", ["index", "freq", "day_count"])
ibor_swap_indices = [
    IRSConventions(indices.BBSW3M, ql.Period("3M"), DayCount.ACT365F),
    IRSConventions(indices.BBSW6M, ql.Period("6M"), DayCount.ACT365F),
    IRSConventions(indices.BKBM3M, ql.Period("6M"), DayCount.ACT365F),
    IRSConventions(indices.BUBOR6M, ql.Period("1Y"), DayCount.ACT365F),
    IRSConventions(indices.CIBOR6M, ql.Period("1Y"), DayCount.THIRTY360_BONDBASIS),
    IRSConventions(indices.EURIBOR3M, ql.Period("1Y"), DayCount.THIRTY360_BONDBASIS),
    IRSConventions(indices.HIBOR3M, ql.Period("3M"), DayCount.ACT365F),
    IRSConventions(indices.JIBAR3M, ql.Period("3M"), DayCount.ACT365F),
    IRSConventions(indices.NIBOR6M, ql.Period("1Y"), DayCount.THIRTY360_BONDBASIS),
    IRSConventions(indices.PRIBOR6M, ql.Period("1Y"), DayCount.ACT365F),
    IRSConventions(indices.STIBOR3M, ql.Period("1Y"), DayCount.THIRTY360_BONDBASIS),
    IRSConventions(indices.TIIE28D, ql.Period("1Y"), DayCount.ACT360),
    IRSConventions(indices.WIBOR6M, ql.Period("1Y"), DayCount.ACTACT_ISDA),
]
ibor_swap_families = []
for ibor_swp_conv in ibor_swap_indices:
    swap_family = IRSwapFamily(
        name=f"IRS-{ibor_swp_conv.index.name}",
        index=ibor_swp_conv.index,
        day_count=ibor_swp_conv.day_count,
        frequency=ibor_swp_conv.freq.frequency(),
    )
    ibor_swap_families.append(swap_family)

for swap_family in ibor_swap_families:
    StateManager.store(InstrumentFamily, swap_family)
    for term in swap_tenors:
        i = InstrumentType(family=swap_family, specifics=Term.from_ql(term))
        StateManager.store(InstrumentType, i)

#
# basis swaps
#
basis_swap_families = []
# ESTR-EURIBOR
for tenor in [1, 3, 6, 12]:
    swap_family = IRBasisSwapFamily(
        name=f"IRS-ESTR-EURIBOR{tenor}M",
        index1=indices.ESTR,
        index2=getattr(indices, f"EURIBOR{tenor}M"),
    )
    basis_swap_families.append(swap_family)
# EURIBOR-EURIBOR
for tenor1 in [1, 3, 6, 12]:
    for tenor2 in [1, 3, 6, 12]:
        if tenor2 <= tenor1:
            continue
        swap_family = IRBasisSwapFamily(
            name=f"IRS-EURIBOR{tenor1}M-EURIBOR{tenor2}M",
            index1=getattr(indices, f"EURIBOR{tenor1}M"),
            index2=getattr(indices, f"EURIBOR{tenor2}M"),
        )
        basis_swap_families.append(swap_family)

for swap_family in basis_swap_families:
    StateManager.store(InstrumentFamily, swap_family)
    for term in swap_tenors:
        i = InstrumentType(family=swap_family, specifics=Term.from_ql(term))
        StateManager.store(InstrumentType, i)


#
# bond conventions
#
StateManager.store(
    BondType,
    BondType(
        name="Govt-USA",
        description="US Treasury Bond",
        currency=Currency.USD,
        frequency=Frequency.SEMIANNUAL,
        day_count=DayCount.ACTACT_BOND,
        settlement_delay=2,
        period_adjust=ql.ModifiedFollowing,
        calendar=Calendar(ql_calendar_id=("UnitedStates", "GovernmentBond")),
    ),
)

StateManager.store(
    BondType,
    BondType(
        name="Corp-USA",
        description="US Corporate Bond",
        currency=Currency.USD,
        frequency=Frequency.SEMIANNUAL,
        day_count=DayCount.THIRTY360_USA,
        settlement_delay=2,
        period_adjust=ql.ModifiedFollowing,
        calendar=Calendar(ql_calendar_id=("UnitedStates", "Settlement")),
    ),
)

StateManager.store(
    BondType,
    BondType(
        name="FRN-SOFR",
        description="SOFR FRN",
        currency=Currency.USD,
        frequency=Frequency.ANNUAL,
        day_count=DayCount.ACT360,
        settlement_delay=0,
        period_adjust=ql.ModifiedFollowing,
        calendar=Calendar(ql_calendar_id=("UnitedStates", "Settlement")),
        index=indices.SOFR,
    ),
)

StateManager.store(
    BondType,
    BondType(
        name="Govt-UK",
        description="UK Gilt",
        currency=Currency.GBP,
        frequency=Frequency.SEMIANNUAL,
        day_count=DayCount.ACTACT_ISMA,
        settlement_delay=1,
        period_adjust=ql.Unadjusted,
        payment_adjust=ql.Unadjusted,
        endOfMonthFlag=True,
        calendar=Calendar(ql_calendar_id=("UnitedKingdom", "Settlement")),
    ),
)

StateManager.store(
    BondType,
    BondType(
        name="Corp-UK",
        description="United Kingdom Corporate Bond",
        currency=Currency.GBP,
        frequency=Frequency.ANNUAL,
        day_count=DayCount.ACT365F,
        settlement_delay=2,
        period_adjust=ql.ModifiedFollowing,
        calendar=Calendar(ql_calendar_id=("UnitedKingdom", "Settlement")),
    ),
)


# TODO use proper day counts and calendars for cash and swaps
def _create_zero_coupon_instruments():
    # reasonable set of currencies as determined
    # by which bonds show up in global FI ETFs
    _currencies = [
        Currency.EUR,
        Currency.GBP,
        Currency.USD,
        Currency.MXN,
        Currency.CHF,
        Currency.CNY,
        Currency.SEK,
        Currency.JPY,
        Currency.NZD,
        Currency.CAD,
        Currency.AUD,
        Currency.SGD,
        Currency.KRW,
        Currency.IDR,
        Currency.THB,
        Currency.MYR,
        Currency.PLN,
        Currency.DKK,
        Currency.PEN,
        Currency.NOK,
        Currency.ILS,
        Currency.RON,
        Currency.COP,
        Currency.CLP,
        Currency.CZK,
        Currency.HUF,
        Currency.BRL,
        Currency.ZAR,
        Currency.EGP,
        Currency.TRY,
        Currency.ARS,
        Currency.RUB,
        Currency.PHP,
        Currency.HKD,
    ]
    for ccy in _currencies:
        zc_family = ZeroCouponBondFamily(name=f"ZCB-{ccy.name}", currency=ccy, settlement_delay=0)
        StateManager.store(InstrumentFamily, zc_family)
        for iterm in zc_bond_tenors:
            ifam = InstrumentType(family=zc_family, specifics=Term.from_ql(iterm))
            StateManager.store(InstrumentType, ifam)
    for ccy in _currencies:
        cash_family = CashDepoFamily(name=f"Cash-{ccy.name}", currency=ccy, settlement_delay=2)
        StateManager.store(InstrumentFamily, zc_family)
        for iterm in cash_tenors:
            ifam = InstrumentType(family=cash_family, specifics=Term.from_ql(iterm))
            StateManager.store(InstrumentType, ifam)


_create_zero_coupon_instruments()
