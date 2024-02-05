# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
test Quote databases functionality
"""

from aqumenlib import Date
from aqumenlib.schema import quote_db

def test_quote_db():
    """
    Test storing quotes using in-memory DB,
    then binding them to instruments.
    """
    pricing_date = Date.from_any("2023-11-17")

    quote_db.db_init(":memory:")
    quote_db.save_quotes(
        instruments=[
            ("IRS-SOFR-30Y", 0.057),
            ("IRS-SOFR-1Y", 0.045),
            ("IRS-SOFR-5Y", 0.052),
        ],
        quote_date=pricing_date,
    )

    instruments = quote_db.bind_instruments(
        quote_date=pricing_date,
        instrument_types=[
            "IRS-SOFR-1Y",
            "IRS-SOFR-5Y",
            "IRS-SOFR-30Y",
        ],
    )

    assert len(instruments) == 3
    assert instruments[0].quote == 0.045
    assert instruments[1].quote == 0.052
    assert instruments[2].quote == 0.057

