# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
test bond functionality
"""

from aqumenlib.state import list_objects
from aqumenlib.instrument_family import InstrumentFamily


def test_list_objects():
    """
    Test listing of aqumenlib-managed objects
    """
    big_list = list_objects(InstrumentFamily)
    assert "FUT-ICE-EON" in big_list
    assert "IRS-CORRA" in big_list
    short_list = list_objects(InstrumentFamily, matches="CORRA")
    assert "FUT-ICE-EON" not in short_list
    assert "IRS-CORRA" in short_list
