# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import os
import sys
import logging

import aqumenlib.config as cfg
from aqumenlib.config_logs import init_logging

if not any("pytest" in arg for arg in sys.argv):
    init_logging(cfg.as_dict())
else:
    print("Detected pytest. Disabling init.")

from aqumenlib.enums import (
    QuoteConvention,
    AssetClass,
    RiskType,
    Metric,
    QuoteBumpType,
    RateInterpolationType,
    Frequency,
    BusinessDayAdjustment,
)
from aqumenlib.date import Date, DateInput
from aqumenlib.term import Term
from aqumenlib.calendar import Calendar
from aqumenlib.daycount import DayCount
from aqumenlib.currency import Currency
from aqumenlib.cashflow import Cashflow
from aqumenlib.index import Index, RateIndex
from aqumenlib.instrument_family import InstrumentFamily
from aqumenlib.instrument_type import InstrumentType
from aqumenlib.instrument import Instrument
from aqumenlib.curve import Curve
from aqumenlib.market import MarketView
from aqumenlib.trade import TradeInfo
from aqumenlib.pricer import (
    Pricer,
    set_global_reporting_currency,
    get_global_reporting_currency,
)
import aqumenlib.instruments.builtins
