# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from enum import Enum, auto, unique


@unique
class Frequency(Enum):
    """
    Frequency for payments and schedules.
    """

    NOFREQUENCY = -1
    ONCE = 0
    ANNUAL = 1
    SEMIANNUAL = 2
    EVERYFOURTHMONTH = 3
    QUARTERLY = 4
    BIMONTHLY = 6
    MONTHLY = 12
    EVERYFOURTHWEEK = 13
    BIWEEKLY = 26
    WEEKLY = 52
    DAILY = 365
    OTHERFREQUENCY = 999

    def to_ql(self):
        """
        Get an equivalent QuantLib representation.
        """
        return self.value


@unique
class TimeUnit(Enum):
    """
    Time units to be used with definitions of terms and tenors.
    """

    DAYS = 0
    WEEKS = 1
    MONTHS = 2
    YEARS = 3
    HOURS = 4
    MINUTES = 5
    SECONDS = 6
    MILLISECONDS = 7
    MICROSECONDS = 8

    def to_ql(self):
        """
        Get an equivalent QuantLib representation.
        """
        return self.value


@unique
class BusinessDayAdjustment(Enum):
    """
    Business day adjustment rule.
    """

    FOLLOWING = 0
    MODIFIEDFOLLOWING = 1
    PRECEDING = 2
    MODIFIEDPRECEDING = 3
    UNADJUSTED = 4
    HALFMONTHMODIFIEDFOLLOWING = 5
    NEAREST = 6

    def to_ql(self):
        """
        Get an equivalent QuantLib representation.
        """
        return self.value


@unique
class AssetClass(Enum):
    """
    Asset class categorization.
    """

    EQUITY = 1
    BOND = 2
    COMMODITY = 3
    RATE = 4
    INFLATION = 5
    FX = 6
    CASH = 10
    CRYPTO = 20


@unique
class RiskType(Enum):
    """
    Classification for different types of market risk.
    """

    EQUITY = 1
    BOND = 2
    COMMODITY = 3
    RATE = 4
    RATEBASIS = 5
    CREDIT = 6
    INFLATION = 7
    FX = 8
    DEFAULT = 30
    CRYPTO = 50


@unique
class QuoteConvention(Enum):
    """
    Qualifier to quotes which allows for
    correct interpretation of numbers.
    """

    Unspecified = 0
    CleanPrice = 1
    DirtyPrice = 2
    Yield = 3


@unique
class QuoteBumpType(Enum):
    """
    Qualifier to quote bump which allows for
    correct interpretation of numbers.
    """

    ABSOLUTE = 1
    RELATIVE = 2
    FIXED = 3


@unique
class Metric(Enum):
    """
    List of result types that all pricers will accept.

    The first set of these deal with various ways in which valuations
    can be obtained. Market value means that valuations can be
    taken directly from the market quotes - such as current quote for a
    given bond or futures contract. Model value means that market quotes
    are ignored for a security, i.e. a bond would be valued by discounting
    its cash flows with rate and credit curves, futures might be interpolated
    from a forward curves, etc. If a VALUE request is prefixed with NATIVE
    it means that if the product has single native currency, the result
    will be a single number representing value in that currency. REPORTING
    values use the reporting currency setting to convert all valuations
    into single reporting currency. VALUE requests that are not prefixed
    with either NATIVE or REPORTING return a list of tuples of currency and value
    pairs, so that for multi-currency products value in each currency can be obtained.

    """

    VALUE = auto()
    MARKET_VALUE = auto()
    MODEL_VALUE = auto()
    NATIVE_MARKET_VALUE = auto()
    NATIVE_MODEL_VALUE = auto()
    REPORTING_VALUE = auto()
    REPORTING_MARKET_VALUE = auto()
    REPORTING_MODEL_VALUE = auto()
    RISK_VALUE = auto()
    CURRENCY = auto()
    CASHFLOWS = auto()
    IRR = auto()
    YIELD = auto()
    DURATION = auto()
    DURATION_MACAULAY = auto()
    CONVEXITY = auto()
    ZSPREAD = auto()
    # DV01 = auto() # TODO DV01, Inflation01


@unique
class RateInterpolationType(Enum):
    """
    Interpolation types for rate curves.
    """

    PiecewiseFlatForward = auto()
    PiecewiseLinearForward = auto()
    PiecewiseLogLinearDiscount = auto()
    PiecewiseLinearZero = auto()
    PiecewiseCubicZero = auto()
    PiecewiseLogCubicDiscount = auto()
    PiecewiseSplineCubicDiscount = auto()
    PiecewiseKrugerZero = auto()
    PiecewiseKrugerLogDiscount = auto()
    PiecewiseConvexMonotoneZero = auto()
    PiecewiseNaturalCubicZero = auto()
    PiecewiseNaturalLogCubicDiscount = auto()
    PiecewiseLogMixedLinearCubicDiscount = auto()
