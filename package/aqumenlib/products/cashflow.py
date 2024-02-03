# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Cash related pricers such as cashflow pricers, bank accounts, etc
"""
from typing import List
import bisect


from aqumenlib import (
    Date,
    Currency,
)
from aqumenlib.cashflow import Cashflow


class CashflowBuckets:
    """
    Combine cash flows into a limited number of buckets
    represented by fixed cash flow objects.
    Meant to be used with cash flows of the same currency and will raise error otherwise.
    """

    def __init__(self, currency: Currency, anchor_date: Date) -> None:
        self.buckets = []
        self.currency = currency
        # generate dates for buckets - to be made configurable in the future
        self.anchor_xl = anchor_date.to_excel()
        # weekly for the first year
        for i in range(0, 52):
            self.buckets.append(
                Cashflow(
                    currency=currency,
                    date=Date.from_excel(self.anchor_xl + i * 7),
                    amount=0.0,
                    notional=None,
                )
            )
        # then every 4 weeks for about 30 years
        for i in range(0, 360):
            self.buckets.append(
                Cashflow(
                    currency=currency,
                    date=Date.from_excel(self.anchor_xl + 52 * 7 + i * 28),
                    amount=0.0,
                    notional=None,
                )
            )
        self.bucket_xl_dates = [b.date.to_excel() for b in self.buckets]

    def add_flow(self, f: Cashflow) -> None:
        """
        Accepts a flow and adds it to corresponding time buckets.
        Silently ignores any flows occuring before the anchor date.
        """
        if f.currency != self.currency:
            raise KeyError("Flow currency does not match bucket currency")
        d = f.date.to_excel()

        if d < self.anchor_xl:
            return
        i = min(
            len(self.bucket_xl_dates) - 1,
            bisect.bisect_left(self.bucket_xl_dates, d),
        )
        self.buckets[i].amount += f.amount

    def add_flows(self, flows: List[Cashflow]) -> None:
        """
        Accepts a list of flows and adds them to corresponding time buckets.
        """
        for f in flows:
            self.add_flow(f)

    def get_flows(self) -> List[Cashflow]:
        return list(filter(lambda x: x.amount != 0.0, self.buckets))
