# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

import pydantic
from typing import Any, Optional

from aqumenlib.date import Date, DateInput


class TradeInfo(pydantic.BaseModel):
    """
    Any trade specifics that are separate from the underlying product or security.
    Objects of TradeInfo class are typically supplied together with the
    underlying security when forming a pricer.
    """

    trade_id: Optional[str] = None
    amount: float = 100.0
    is_receive: bool = True
    price: float = 0.0
    trade_date: Optional[DateInput] = None
    settle_date: Optional[DateInput] = None
    counterparty_name: Optional[str] = None
    csa_id: Optional[str] = None  # credit support annex, or collateral type

    def __eq__(self, other):
        if not isinstance(other, TradeInfo):
            return False
        return (
            self.trade_id == other.trade_id
            and self.amount == other.amount
            and self.is_receive == other.is_receive
            and self.price == other.price
            and self.trade_date == other.trade_date
            and self.settle_date == other.settle_date
            and self.counterparty_name == other.counterparty_name
            and self.csa_id == other.csa_id
        )
