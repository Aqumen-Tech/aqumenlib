# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
BondType class
"""

from typing import Any, Optional
from typing_extensions import Annotated
import pydantic
from pydantic.functional_validators import BeforeValidator

import QuantLib as ql

from aqumenlib import (
    Currency,
    Frequency,
    BusinessDayAdjustment,
)
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.state import StateManager
from aqumenlib.namedobject import NamedObject
from aqumenlib.index import RateIndex, InflationIndex


class BondType(pydantic.BaseModel, NamedObject):
    """
    Class that encapsulates basic bond conventions.
    Bond type would capture all that is needed to set up a bond
    such as SOFR FRN, UK Inflation Gilt, or US T-Bill.
    By providing specific coupon and maturity, bond type can
    be used to construct a bond object.
    """

    name: str
    description: str
    currency: Currency
    frequency: Frequency
    day_count: DayCount
    day_count_ai: Optional[DayCount] = None
    settlement_delay: int
    period_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    payment_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    maturity_adjust: BusinessDayAdjustment = BusinessDayAdjustment.UNADJUSTED
    calendar: Calendar
    endOfMonthFlag: bool = True
    index: Optional[RateIndex | InflationIndex] = None

    def model_post_init(self, __context):
        if self.day_count_ai is None:
            self.day_count_ai = self.day_count

    def get_name(self):
        return self.name

    def ql_day_count(self):
        """
        QuantLib object for day count
        """
        return self.day_count.to_ql()


def inputconverter_bond_type(v: Any) -> BondType:
    """
    Convert any valid input to BondType
    """
    if isinstance(v, BondType):
        return v
    elif isinstance(v, str):
        return StateManager.get(BondType, v)
    elif isinstance(v, dict):
        return BondType.model_validate(v)
    else:
        raise pydantic.ValidationError(f"Could not convert input to BondType: {v}")


BondTypeInput = Annotated[BondType, BeforeValidator(inputconverter_bond_type)]


def create_generic_bond_type(ccy: Currency):
    """
    Utility to create generic bond type in a given currency, useful for testing
    or capturing generic risk behaviors.
    """
    bt = BondType(
        name=f"Generic-{ccy.name}",
        description=f"Generic {ccy.name} Bond",
        currency=ccy,
        frequency=ql.Semiannual,
        day_count=DayCount.ACT365F,
        settlement_delay=2,
        period_adjust=ql.ModifiedFollowing,
        calendar=Calendar(ql_calendar_id="NullCalendar"),
    )
    return bt
