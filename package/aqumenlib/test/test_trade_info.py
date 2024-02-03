# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from aqumenlib.trade import TradeInfo


def test_trade_compare():
    trade1 = TradeInfo(
        trade_id="T1234",
        trade_date="2023-09-06",
        settle_date="2023-09-07",
        counterparty_name="PartyA",
        csa_id="CSA2021",
        amount=1000,
    )
    trade2 = TradeInfo(
        trade_id="T1235",
        trade_date="2023-09-06",
        settle_date="2023-09-07",
        counterparty_name="PartyB",
        csa_id="CSA2021",
        amount=1500,
    )
    trade3 = TradeInfo(
        trade_id="T1234",
        trade_date="2023-09-06",
        settle_date="2023-09-07",
        counterparty_name="PartyA",
        csa_id="CSA2021",
        amount=1000,
    )
    assert trade1 != trade2
    assert trade1 == trade3
