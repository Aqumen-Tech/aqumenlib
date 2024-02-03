# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024


from aqumenlib import (
    Date,
    Currency,
)
from aqumenlib.cashflow import Cashflow

from aqumenlib.products.cashflow import CashflowBuckets


def test_cashflow_bucketing():
    """
    Basic test for CashflowBuckets class
    """
    anchor_date = Date.from_isoint(20231025)
    b = CashflowBuckets(currency=Currency.USD, anchor_date=anchor_date)
    total = 0
    wal = 0
    test_flows = [
        (20231025, 10),
        (20231026, 10),
        (20231029, 12),
        (20231229, 10),
        (20231228, 7),
        (20240505, 100),
        (20240506, 200),
        (20440107, 1500),
        (20440107, 1500),
    ]
    for f in test_flows:
        b.add_flow(
            Cashflow(
                currency=Currency.USD,
                date=Date.from_isoint(f[0]),
                amount=f[1],
                notional=None,
            )
        )
        total += f[1]
        wal += f[1] * (Date.from_isoint(f[0]).to_excel() - anchor_date.to_excel()) / 365.0
    wal = wal / total

    test_wal = 0
    test_total = 0
    flows = b.get_flows()
    assert len(flows) == 5

    for f in flows:
        test_total += f.amount
        test_wal += f.amount * (f.date.to_excel() - b.anchor_xl) / 365.0
        print(f)
    test_wal = test_wal / test_total

    assert test_total == total
    assert test_wal > wal
    assert test_wal < 19 and test_wal > 18
    assert test_wal - wal < 30.0 / 365.0
