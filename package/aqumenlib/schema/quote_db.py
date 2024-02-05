# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

from datetime import timedelta
import datetime
from typing import List, Tuple
import pathlib
from peewee import Model, DatabaseProxy, SqliteDatabase
from peewee import IntegerField, DoubleField, CharField
import pandas as pd
import pydantic

from aqumenlib.date import date_from_isoint, date_to_isoint, Date
from aqumenlib import QuoteConvention
from aqumenlib.instrument import Instrument
from aqumenlib.instrument_type import InstrumentTypeInput

dbproxy = DatabaseProxy()


class Quote(Model):
    """
    Schema for daily market quotes
    """

    quote_date = IntegerField()
    instrument_id = CharField(max_length=150)
    quote = DoubleField()
    quote_type = CharField(
        max_length=25,
        help_text="Nature of the quote - e.g. CLOSE, MID, BID, ASK, FIXING - from QuoteType Enum",
    )
    quote_convention = CharField(
        max_length=25,
        default="",
        help_text="Which way of representing the qouote is used e.g. Yield or Clean, from QuoteConvention Enum",
    )
    source = CharField(max_length=25, help_text="Provider's ID, from DataSource Enum")
    entitlement_id = IntegerField(
        default=0,
        help_text="Ownership information to allow restriction of access by user or organization",
    )
    added_timestamp = DoubleField(
        help_text="timestamp is used only for figuring out which quote is the latest for a given day"
    )

    class Meta:
        """
        PeeWee table meta
        """

        database = dbproxy
        # index based on date+ID, eg: 20230616-OIS-FedFunds-10Y
        indexes = ((("quote_date", "instrument_id"), False),)

    def __repr__(self):
        return (
            f"Quote(quote_date={self.quote_date}, "
            f"instrument_id={self.instrument_id}, "
            f"quote={self.quote}, "
            f"quote_type={self.quote_type}, "
            f"quote_convention={self.quote_convention}, "
            f"source={self.source}, "
            f"added_timestamp={self.added_timestamp})"
        )

    def __str__(self):
        return f"{self.instrument_id} on {self.quote_date} is {self.quote} {self.quote_type}"

    def get_quote_convention(self) -> QuoteConvention:
        """
        Determine quote convention if supplied in the database.
        Otherwise make a best guess, e.g. assume full price for bonds.
        """
        if self.quote_convention:
            return QuoteConvention[self.quote_convention]
        elif self.instrument_id.startswith("IRS"):
            return QuoteConvention.Yield
        else:
            return QuoteConvention.DirtyPrice


def init_proxy(db):
    """
    Initialize the proxy database for this table.
    Should not be called by users directly - see db_init() and db_init_from_config() instead.
    """
    global dbproxy  # pylint: disable=global-variable-not-assigned
    dbproxy.initialize(db)
    db.create_tables([Quote])


def db_init_from_config(cfg_dict):
    """
    Initialize the database using supplied user config.
    """
    if not "data" in cfg_dict:
        return
    if cfg_dict["data"]["db_type"] == "sqlite":
        db_init(cfg_dict["data"]["sqlite_dir"])
    else:
        raise NotImplementedError("Support for databases other than SQLite not implemented yet")


def db_init(db_location_folder):
    """
    Initialize the database using provided folder where to place the file.
    If folder is given as :memory: then in-memory, in-process SQLite DB is initialized.
    """
    if db_location_folder == ":memory:":
        db = SqliteDatabase(":memory:")
        db.connect()
        init_proxy(db)
        return

    db_location = pathlib.Path(db_location_folder)
    db_location.mkdir(exist_ok=True)
    #
    # cache_size (when a positive number) is in pages, with 1000 pages =~ 4MB
    #
    quotes_db = SqliteDatabase(
        str(db_location / "quotes.db"),
        pragmas={
            "journal_mode": "wal",
            "cache_size": 15000,
        },
    )
    quotes_db.connect()
    init_proxy(quotes_db)


def save_new_quote(
    inst: str,
    quote_dt: Date,
    quote_value: float,
    quote_type: str,
    quote_source: str,
    ignore_if_exists: bool = True,
) -> None:
    """
    Saves a new quote to the database.
    If ignore_if_exists is True, first this function will check if
    a quote for the same instrument / date already exists, and if it does,
    no further action is taken (i.e. new quote is not saved).
    """
    qdt = quote_dt.to_isoint()
    if ignore_if_exists and check_existsence(qdt, inst):
        return
    quote = Quote(
        quote_date=qdt,
        added_timestamp=datetime.datetime.utcnow().timestamp(),
        instrument_id=inst,
        quote=quote_value,
        quote_type=quote_type,
        source=quote_source,
    )
    quote.save()


def save_quotes(
    instruments: List[Tuple[str, float]],
    quote_date: Date,
    quote_type: str = "",
    quote_source: str = "",
    ignore_if_exists: bool = True,
) -> None:
    """
    Save a set of quotes for given instruments.
    """
    for i, q in instruments:
        save_new_quote(i, quote_date, q, quote_type, quote_source, ignore_if_exists)


def get_quote(date: Date, instrument_id: str, sources: List[str] = None, window: int = 0) -> Quote:
    """
    Look up quote in the database, using optional list of source as a priority list
    to decide which quotes to return first.
    Window argument can be used to allow for quote to be found within a fixed time window,
    for example a window of 2 means that the quote will be searched within the last two days.
    """
    if window == 0:
        quotes = Quote.select().where((Quote.quote_date == date.to_isoint()) & (Quote.instrument_id == instrument_id))
    elif window > 0:
        start_date = date_to_isoint(date.to_py() - timedelta(days=window))
        end_date = date.to_isoint()
        quotes = (
            Quote.select()
            .where((start_date <= Quote.quote_date <= end_date) & (Quote.instrument_id == instrument_id))
            .order_by(-Quote.quote_date)
        )
    else:
        raise LookupError("Quote lookup window cannot be negative")
    if len(quotes) == 0:
        return None
    d = quotes[0].quote_date

    if sources is not None:
        for quote_source in sources:
            filtered_quotes = filter(lambda q: q.source == quote_source and q.quote_date == d, quotes)
            if filtered_quotes:
                latest_quote = max(filtered_quotes, key=lambda q: q.added_timestamp)
                print(latest_quote)
                return latest_quote

    latest_quote = max(quotes, key=lambda q: q.added_timestamp)
    return latest_quote


def check_existsence(date: int, instrument_id: str):
    """
    Return true if quote exists for a given instrument on given date.
    """
    quotes = Quote.select().where((Quote.quote_date == date) & (Quote.instrument_id == instrument_id))
    if len(quotes) >= 1:
        return True
    return False


@pydantic.validate_call
def bind_instruments(
    quote_date: Date,
    instrument_types: List[InstrumentTypeInput],
    window: int = 0,
) -> List[Instrument]:
    """
    Given a list of InstrumentType objects, find corresponding quotes and return a list of instruments.
    """
    _instruments = []
    for instrument_type in instrument_types:
        quote = get_quote(date=quote_date, instrument_id=instrument_type.get_name(), window=window)
        inst = Instrument.from_type(instrument_type, quote.quote)
        _instruments.append(inst)
    return _instruments


def quotes_query(
    instrument: str = None,
    min_date: datetime.date = None,
    max_date: datetime.date = None,
):
    """
    Select a list of quotes matching optional criteria
    """
    query = Quote.select()

    if instrument:
        query = query.where(Quote.instrument_id % instrument)

    if min_date is not None:
        min_date = date_to_isoint(min_date)
        query = query.where(Quote.quote_date >= min_date)

    if max_date is not None:
        max_date = date_to_isoint(max_date)
        query = query.where(Quote.quote_date <= max_date)

    query = query.order_by(-Quote.quote_date)
    quotes = [q for q in query]
    return quotes


def quotes_to_dataframe(quotes: List[Quote]) -> pd.DataFrame:
    """
    Convert a list of Quote objects to a DataFrame.
    """
    list_of_dicts = []
    for q in quotes:
        list_of_dicts.append(
            {
                "Date": date_from_isoint(q.quote_date),
                "Instrument": q.instrument_id,
                "Quote": q.quote,
                "Quote Type": q.quote_type,
                "Source": q.source,
                "Added": datetime.datetime.fromtimestamp(q.added_timestamp).strftime("%a %d %b %Y, %I:%M%p"),
            }
        )
    df = pd.DataFrame(list_of_dicts)
    return df
