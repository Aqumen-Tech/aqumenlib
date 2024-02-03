# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from aqumenlib.currency import Currency, get_ql_currency, get_ql_currency_from_str


def test_ccys():
    """
    Smoke tests for currency type.
    """
    assert get_ql_currency(Currency.EUR).code() == "EUR"
    assert get_ql_currency(Currency.EUR).numericCode() == 978
    assert get_ql_currency_from_str("GBP").code() == "GBP"
    assert get_ql_currency_from_str("GBP").name() == "British pound sterling"
    ql_euro = get_ql_currency(Currency.EUR)
    assert Currency[ql_euro.code()] == Currency.EUR
    assert Currency(978) == Currency.EUR
