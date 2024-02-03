# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import QuantLib as ql
import datetime as dt

calendar = ql.UnitedKingdom()
dayCounter = ql.ActualActual(ql.ActualActual.Bond)
convention = ql.ModifiedFollowing
lag = 3

today = ql.Date(5, 3, 2008)
evaluationDate = calendar.adjust(today)
issue_date = calendar.advance(evaluationDate, -1, ql.Years)
maturity_date = ql.Date(2, 9, 2052)
fixing_date = calendar.advance(evaluationDate, -lag, ql.Months)

ql.Settings.instance().setEvaluationDate(evaluationDate)
yTS = ql.YieldTermStructureHandle(ql.FlatForward(evaluationDate, 0.05, dayCounter))

tenor = ql.Period(1, ql.Months)

from_date = ql.Date(20, ql.July, 2007)
to_date = ql.Date(20, ql.November, 2009)
rpiSchedule = ql.Schedule(
    from_date,
    to_date,
    tenor,
    calendar,
    convention,
    convention,
    ql.DateGeneration.Backward,
    False,
)

# this is the going to be holder the inflation curve.
cpiTS = ql.RelinkableZeroInflationTermStructureHandle()
inflationIndex = ql.UKRPI(False, cpiTS)
fixData = [
    206.1,
    207.3,
    208.0,
    208.9,
    209.7,
    210.9,
    209.8,
    211.4,
    212.1,
    214.0,
    215.1,
    216.8,
    216.5,
    217.2,
    218.4,
    217.7,
    216,
    212.9,
    210.1,
    211.4,
    211.3,
    211.5,
    212.8,
    213.4,
    213.4,
    213.4,
    214.4,
]
dte_fixings = [dtes for dtes in rpiSchedule]
print(len(fixData))
print(len(dte_fixings[: len(fixData)]))
# must be the same length
# inflationIndex.addFixings(dte_fixings[:len(fixData)], fixData)
# Current CPI level
# last observed rate
fixing_rate = 214.4


inflationIndex.addFixing(fixing_date, fixing_rate)

observationLag = ql.Period(lag, ql.Months)
zciisData = [
    (ql.Date(25, ql.November, 2010), 3.0495),
    (ql.Date(25, ql.November, 2011), 2.93),
    (ql.Date(26, ql.November, 2012), 2.9795),
    (ql.Date(25, ql.November, 2013), 3.029),
    (ql.Date(25, ql.November, 2014), 3.1425),
    (ql.Date(25, ql.November, 2015), 3.211),
    (ql.Date(25, ql.November, 2016), 3.2675),
    (ql.Date(25, ql.November, 2017), 3.3625),
    (ql.Date(25, ql.November, 2018), 3.405),
    (ql.Date(25, ql.November, 2019), 3.48),
    (ql.Date(25, ql.November, 2021), 3.576),
    (ql.Date(25, ql.November, 2024), 3.649),
    (ql.Date(26, ql.November, 2029), 3.751),
    (ql.Date(27, ql.November, 2034), 3.77225),
    (ql.Date(25, ql.November, 2039), 3.77),
    (ql.Date(25, ql.November, 2049), 3.734),
    (ql.Date(25, ql.November, 2059), 3.714),
]

# lRates=[rtes/100.0 for rtes in zip(*zciisData)[1]]
# baseZeroRate = lRates[0]

zeroSwapHelpers = [
    ql.ZeroCouponInflationSwapHelper(
        ql.QuoteHandle((ql.SimpleQuote(rate / 100))),
        observationLag,
        date,
        calendar,
        convention,
        dayCounter,
        inflationIndex,
        ql.CPI.AsIndex,
        yTS,
    )
    for date, rate in zciisData
]


# the derived inflation curve
jj = ql.PiecewiseZeroInflation(
    evaluationDate,
    calendar,
    dayCounter,
    observationLag,
    inflationIndex.frequency(),
    zciisData[0][1],  # baseZeroRate,
    zeroSwapHelpers,
    1.0e-12,
    ql.Linear(),
)

cpiTS.linkTo(jj)

notional = 1000000

fixedRates = [0.1]

fixedDayCounter = ql.Actual365Fixed()
fixedPaymentConvention = ql.ModifiedFollowing
fixedPaymentCalendar = ql.UnitedKingdom()
contractObservationLag = ql.Period(3, ql.Months)
observationInterpolation = ql.CPI.Flat
settlementDays = 3
growthOnly = False

baseCPI = 206.1


fixedSchedule = ql.Schedule(
    issue_date,
    maturity_date,
    ql.Period(ql.Semiannual),
    fixedPaymentCalendar,
    ql.Unadjusted,
    ql.Unadjusted,
    ql.DateGeneration.Backward,
    False,
)

bond = ql.CPIBond(
    settlementDays,
    notional,
    growthOnly,
    baseCPI,
    contractObservationLag,
    inflationIndex,
    observationInterpolation,
    fixedSchedule,
    fixedRates,
    fixedDayCounter,
    fixedPaymentConvention,
)

# bond2= ql.QuantLib.C

bondEngine = ql.DiscountingBondEngine(yTS)
bond.setPricingEngine(bondEngine)
print(bond.NPV())
print(bond.cleanPrice())
compounding = ql.Compounded
yield_rate = bond.bondYield(fixedDayCounter, compounding, ql.Semiannual)
y_curve = ql.InterestRate(yield_rate, fixedDayCounter, compounding, ql.Semiannual)
##Collate results
print("Clean Price:", bond.cleanPrice())
print("Notional:", bond.notional())
print("Yield:", yield_rate)
print("Accrued Amount:", bond.accruedAmount())
print("Settlement Value:", bond.settlementValue())

# suspect there's more to this for TIPS
print("Duration:", ql.BondFunctions.duration(bond, y_curve))
print("Convexity:", ql.BondFunctions.convexity(bond, y_curve))
print("Bps:", ql.BondFunctions.bps(bond, y_curve))
print("Basis Point Value:", ql.BondFunctions.basisPointValue(bond, y_curve))
print("Yield Value Basis Point:", ql.BondFunctions.yieldValueBasisPoint(bond, y_curve))

print("NPV:", bond.NPV())

# get the cash flows:
# cf_list=[(cf.amount(),cf.date()) for cf in bond.cashflows()]


def to_datetime(d):
    return dt.datetime(d.year(), d.month(), d.dayOfMonth())


for cf in bond.cashflows():
    try:
        amt = cf.amount()
        rte = jj.zeroRate(cf.date())
        zc = yTS.zeroRate(cf.date(), fixedDayCounter, compounding, ql.Semiannual).rate()
    except:
        amt = 0
        rte = 0
        zc = 0
    print(to_datetime(cf.date()), amt, rte, zc)
