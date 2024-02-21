# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
FX Swap, FX Forward and FX NDF (non-deliverable forward) products
"""

from typing import Any, Optional
import pydantic

from aqumenlib import Date, Currency
from aqumenlib.namedobject import NamedObject


class FXSwap(pydantic.BaseModel, NamedObject):
    """
    FX Swap, FX Forward and FX NDF (non-deliverable forward) products.

    This product describes an FX swap, which consists of two exchanges of cash flows
    in different currencies. At start date, a cash flow of 1 is made in base_currency
    (use TradeInfo in the pricer to scale the notional).
    Other side payments are determined as the base exchange rate (usually spot at inception)
    and forward points determines the exchange at maturity.
    Setting initial_exchange to False effectively turns this product into FX Forward.
    If you also set the optional settlement_currency field, then this product
    will describe a non-deliverable FX forward, where a single cash flow happens
    at maturity date in the settlement currency.
    """

    name: str
    base_currency: Currency
    quote_currency: Currency
    start_date: Date
    maturity_date: Date
    base_fx: float
    forward_points: float
    initial_exchange: bool = True
    settlement_currency: Optional[Currency] = None

    def model_post_init(self, __context: Any) -> None:
        pass

    def get_name(self):
        return self.name
