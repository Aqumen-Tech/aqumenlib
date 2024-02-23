# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Interest Rate Future instruments to be used for calibration
"""

from abc import ABC, abstractmethod
from typing import Optional

import QuantLib as ql
from aqumenlib.calendar import date_adjust, date_advance

from aqumenlib.enums import RateAveraging, BusinessDayAdjustment, TimeUnit
from aqumenlib.exception import AqumenException
from aqumenlib import Date, indices
from aqumenlib.namedobject import NamedObject
from aqumenlib.state import StateManager


class IRFutureContractType(NamedObject):
    """
    Class that implements various ways of calculating relevant dates
    for futures contracts, given contract month.
    """

    def get_name(self):
        """
        Identifier for a contract type
        """
        return f"{self.get_exchange()}-{self.get_symbol()}"

    @abstractmethod
    def get_exchange(self) -> str:
        """
        Return traded exchange, e.g. ICE or Eurex
        """

    @abstractmethod
    def get_symbol(self) -> str:
        """
        Return traded symbol, e.g. SR3
        """

    @abstractmethod
    def get_description(self) -> str:
        """
        Description of this contract
        """

    @abstractmethod
    def get_contract_size(self) -> float:
        """
        Contract size
        """

    @abstractmethod
    def rate_averaging(self) -> RateAveraging:
        """
        Returns rate averaging type of this contract type.
        """

    @abstractmethod
    def get_index(self) -> "RateIndex":
        """
        Returns rate index underlying this contract type.
        """

    @abstractmethod
    def accrual_start_date(self, contract_month: Date) -> Date:
        """
        Returns first accrual date of this contract type.
        """

    @abstractmethod
    def accrual_end_date(self, contract_month: Date) -> Date:
        """
        Returns last accrual date of this contract type.
        """

    @abstractmethod
    def last_trading_date(self, contract_month: Date) -> Date:
        """
        Returns the last trading date of this contract type.
        """


class ICESR1FutureContractType(IRFutureContractType):
    """
    Contracts similar to ICE One-Month SOFR Index Future
    """

    def __init__(self, index, symbol, size, description) -> None:
        self.index = index
        self.contract_symbol = symbol
        self.get_description = description
        self.size = size

    def get_exchange(self) -> str:
        return "ICE"

    def get_symbol(self) -> str:
        return self.contract_symbol

    def get_description(self) -> str:
        return self.get_description

    def get_contract_size(self) -> float:
        return self.size

    def rate_averaging(self) -> RateAveraging:
        return RateAveraging.ARITHMETIC

    def get_index(self) -> "RateIndex":
        return self.index

    def accrual_start_date(self, contract_month: Date) -> Date:
        return contract_month

    def accrual_end_date(self, contract_month: Date) -> Date:
        return Date.end_of_month(contract_month)

    def last_trading_date(self, contract_month: Date) -> Date:
        eom = Date.end_of_month(contract_month)
        eom_bus = date_adjust(eom, self.index.calendar, BusinessDayAdjustment.PRECEDING)
        return eom_bus


class ICESR3FutureContractType(IRFutureContractType):
    """
    Contracts similar to ICE Three-Month SOFR Index Future
    """

    def __init__(self, index, symbol, size, description) -> None:
        self.index = index
        self.contract_symbol = symbol
        self.get_description = description
        self.size = size

    def get_exchange(self) -> str:
        return "ICE"

    def get_symbol(self) -> str:
        return self.contract_symbol

    def get_description(self) -> str:
        return self.get_description

    def get_contract_size(self) -> float:
        return self.size

    def rate_averaging(self) -> RateAveraging:
        return RateAveraging.GEOMETRIC

    def get_index(self) -> "RateIndex":
        return self.index

    def accrual_start_date(self, contract_month: Date) -> Date:
        d = ql.Date.nthWeekday(3, ql.Wednesday, contract_month.month(), contract_month.year())
        return Date.from_ql(d)

    def accrual_end_date(self, contract_month: Date) -> Date:
        d = date_advance(contract_month, 3, TimeUnit.MONTHS)
        d = ql.Date.nthWeekday(3, ql.Wednesday, d.month(), d.year())
        d = date_adjust(Date.from_ql(d), self.index.calendar, BusinessDayAdjustment.PRECEDING)
        return d

    def last_trading_date(self, contract_month: Date) -> Date:
        return self.accrual_end_date(contract_month)


def lookup_contract_type(exchange: str, contract_symbol: str) -> IRFutureContractType:
    """
    Return an instance of IRFutureContractType specialized for a given contract type.
    """
    lookup_id = exchange + "-" + contract_symbol
    return StateManager.get(IRFutureContractType, lookup_id)


# Futures contract month codes to month number mapping
_futures_month_codes = {
    "F": 1,  # January
    "G": 2,  # February
    "H": 3,  # March
    "J": 4,  # April
    "K": 5,  # May
    "M": 6,  # June
    "N": 7,  # July
    "Q": 8,  # August
    "U": 9,  # September
    "V": 10,  # October
    "X": 11,  # November
    "Z": 12,  # December
}


def futures_symbol_to_month_start(symbol: str, anchor_year=Optional[int]) -> Date:
    """
    Converts a futures code to a Date object
    that corresponds to the first calendar day of the month
    that corresponds to the code.

    For example, M25 will be converted to 1-Jun-2025
    """
    try:
        m = _futures_month_codes[symbol[0]]
        y = int(symbol[1:])
        if y > 99 or y < 0:
            raise AqumenException("Year part cannot exceed 99")
        elif y > 9:
            y += 2000
        else:  # y < 10
            # if year is just one digit, this becomes very ambiguous.
            if anchor_year is None:
                raise AqumenException("One digit year requires an anchor year")
            year_now = anchor_year
            in_decade_now = year_now % 10
            if y >= in_decade_now:
                y = in_decade_now + y
            else:
                y = in_decade_now + y + 10
        return Date.from_ymd(y, m, 1)
    except Exception as e:
        raise AqumenException(f"Invalid futures code {symbol}") from e
