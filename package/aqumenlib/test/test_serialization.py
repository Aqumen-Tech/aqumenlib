from aqumenlib import indices
from aqumenlib.calendar import Calendar
from aqumenlib.currency import Currency
from aqumenlib.daycount import DayCount
from aqumenlib.enums import Frequency
from aqumenlib.index import RateIndex
from aqumenlib.instrument import Instrument, create_instrument
from aqumenlib.instrument_type import InstrumentType
from aqumenlib.instruments.irs_family import IRSwapFamily
from aqumenlib.pricers.bond_pricer import BondPricer
from aqumenlib.term import Term
from aqumenlib.test.test_bond import make_uk_gilt_pricer


def test_serialize_instrument():
    """
    Verify that we can serialize instruments.
    """

    fam = IRSwapFamily(
        name="IRS-SONIA",
        index=indices.SONIA,
        day_count=DayCount.ACT365F,
        frequency=Frequency.ANNUAL,
        settlement_delay=1,
    )

    inst1 = InstrumentType(family=fam, specifics=Term.from_str("10Y"))
    dump1 = inst1.model_dump()
    jstxt_1 = inst1.model_dump_json()
    assert "IRS-SONIA-10Y" in jstxt_1
    assert "Sterling Overnight Index Average" in jstxt_1

    inst2 = create_instrument(instrument_type=("IRS-SONIA", "10Y"), quote=0.07)
    dump2 = inst2.model_dump()
    jstxt_2 = inst2.model_dump_json()
    assert dump1 == dump2["inst_type"]
    assert "IRS-SONIA-10Y" in jstxt_2
    assert "Sterling Overnight Index Average" in jstxt_2

    inst_deser = Instrument.model_validate_json(jstxt_2)
    assert inst_deser.name == "IRS-SONIA-10Y"
    assert inst_deser.inst_type.family.name == "IRS-SONIA"
    dump3 = inst_deser.model_dump()
    assert dump3 == dump2
    jstxt_3 = inst_deser.model_dump_json()
    assert "IRS-SONIA-10Y" in jstxt_3
    assert "Sterling Overnight Index Average" in jstxt_3


def test_serialize_index():
    """
    Verify that we can serialize indices.
    """
    a = RateIndex(
        name="AONIA",
        description="Australia Overnight Index Average",
        is_builtin=True,
        currency=Currency.AUD,
        tenor=Term.from_str("1D"),
        days_to_settle=0,
        calendar=Calendar(ql_calendar_id="Australia"),
        day_count=DayCount.ACT365F,
    )

    j = a.model_dump_json()
    assert "Australia Overnight Index Average" in j

    b = RateIndex.model_validate_json(j)
    assert isinstance(b, RateIndex)
    assert b.get_name() == "AONIA"
    assert b.get_currency() == Currency.AUD
    assert b.day_count == DayCount.ACT365F


def test_serialize_bond_pricer():
    """
    Verify that we can serialize bond pricer.
    """
    p = make_uk_gilt_pricer()
    pricer_json = p.model_dump_json()
    v1 = p.value()
    p2 = BondPricer.model_validate_json(pricer_json)
    v2 = p2.value()
    assert v1 == v2
