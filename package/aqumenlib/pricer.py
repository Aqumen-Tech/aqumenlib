# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Base interface for all pricers
"""

from abc import abstractmethod
from typing import Any
import copy
import pydantic
from aqumenlib import Currency, Metric, MarketView
from aqumenlib.namedobject import NamedObject


class PricerSettings(pydantic.BaseModel):
    """
    A settings object that each pricer can use to control some aspects
    of valuation.
    Pricer can have their own settings and there is also a global instance
    that is used by default.
    """

    reporting_currency: Currency


__global_pricer_settings = PricerSettings(reporting_currency=Currency.USD)


def get_global_pricer_settings() -> PricerSettings:
    """
    Returns default global pricer settings.
    """
    return __global_pricer_settings


def get_global_reporting_currency() -> Currency:
    """
    Returns reporting currency from default global pricer settings.
    """
    if __global_pricer_settings.reporting_currency is None:
        raise RuntimeError("Global reporting currency was not set. Use set_global_reporting_currency()")
    return __global_pricer_settings.reporting_currency


def set_global_reporting_currency(ccy: Currency) -> None:
    """
    Sets reporting currency from default global pricer settings.
    """
    __global_pricer_settings.reporting_currency = ccy


class Pricer(NamedObject):  # TODO pydantic
    """
    Common interface for pricer objects
    """

    @abstractmethod
    def calculate(self, metric: Metric) -> Any:
        """
        Returns a result corresponding to a given metric.
        """

    @abstractmethod
    def set_market(self, market_model: "MarketView") -> None:
        """
        Sets or replaces the market model within this pricer.
        """

    @abstractmethod
    def get_market(self) -> "MarketView":
        """
        Returns the market model within this pricer.
        """

    def get_pricer_settings(self) -> PricerSettings:
        """
        Return settings for this pricer.
        """
        return get_global_pricer_settings()

    def new_pricer_for_market(self, market_model: "MarketView"):
        """
        Creates a new pricer by copying this object and replacing it's market model.
        """
        new_pricer = copy.copy(self)
        new_pricer.set_market(market_model)
        return new_pricer
