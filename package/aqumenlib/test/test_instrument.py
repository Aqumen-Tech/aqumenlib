# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Instrument related tests
"""

from aqumenlib.instrument import create_instrument, try_get_tenor_time


def test_tenor_to_time():
    """
    Test for converting instrument specifics to its model time
    """
    for t in ["5 Y", "5Y", "5y", " 5 y"]:
        assert try_get_tenor_time(t) == 5.0
    #
    assert try_get_tenor_time("50Y") == 50.0
    assert try_get_tenor_time("1M") == 1 / 12
    assert try_get_tenor_time("6M") == 1 / 2
    assert try_get_tenor_time("4W") == 28 / 365
    assert try_get_tenor_time("7D") == 7 / 365


def test_convert_instrument():
    """
    Test input conversion of instruments.
    """
    ins1 = create_instrument(instrument_type="IRS-SONIA-10Y", quote=0.07)
    ins2 = create_instrument(instrument_type=("IRS-SONIA", "10Y"), quote=0.07)
    d = ins1.model_dump()
    assert d["name"] == "IRS-SONIA-10Y"
    assert ins1.model_dump() == ins2.model_dump()
