# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Instrument related tests
"""

from aqumenlib.instrument import create_instrument


def test_convert_instrument():
    """
    Test input conversion of instruments.
    """
    ins1 = create_instrument(instrument_type="IRS-SONIA-10Y", quote=0.07)
    ins2 = create_instrument(instrument_type=("IRS-SONIA", "10Y"), quote=0.07)
    d = ins1.model_dump()
    assert d["name"] == "IRS-SONIA-10Y"
    assert ins1.model_dump() == ins2.model_dump()
