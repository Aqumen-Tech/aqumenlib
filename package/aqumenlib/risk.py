# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Facilities for calculting market risk - i.e. sensitivities to market instruments
"""

from typing import List, Optional
from collections import defaultdict
import pydantic
import pandas as pd

from aqumenlib import (
    Currency,
    Pricer,
    Metric,
    AssetClass,
    RiskType,
)
from aqumenlib.instrument import InstrumentFilter, try_get_tenor_time
from aqumenlib.market import MarketView


class RiskResultRow(pydantic.BaseModel):
    """
    Data store for market risk results row
    """

    risk_currency: Currency
    instrument: str
    risk: float
    inst_family: str
    inst_specifics: str
    inst_currency: Currency
    quote: float
    asset_class: AssetClass
    risk_type: RiskType
    tenor_time: Optional[float]

    def to_dict(self):
        """
        Converts this row to a dictionary suitable for DataFrame construction
        """
        dict_for_df = {}
        dict_for_df["Risk Currency"] = self.risk_currency.name
        dict_for_df["Instrument"] = self.instrument
        dict_for_df["Risk"] = self.risk
        dict_for_df["Family"] = self.inst_family
        dict_for_df["Specifics"] = self.inst_specifics
        dict_for_df["Instr Ccy"] = self.inst_currency.name
        dict_for_df["Quote"] = self.quote
        dict_for_df["Asset Class"] = self.asset_class.name
        dict_for_df["Risk Class"] = self.risk_type.name
        dict_for_df["Time"] = self.tenor_time
        return dict_for_df


class RiskResult(pydantic.BaseModel):
    """
    Data store for market risk results - essentially a table stored as list of rows
    and convertible to pandas DataFrame
    """

    rows: List[RiskResultRow] = []

    def __str__(self) -> str:
        df = self.to_dataframe()
        df["Risk"] = df["Risk"].apply(lambda x: f"{x:,.2f}")
        df["Time"] = df["Time"].round(2)
        return str(df.to_string(index=False))

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert results to a pandas dataframe.
        """
        if not self.rows:
            return pd.DataFrame()
        df_data = []
        for row in self.rows:
            df_data.append(row.to_dict())
        df = pd.DataFrame(df_data)
        df = df.sort_values(["Risk Currency", "Family", "Time"])
        return df

    def total_for_family(self, ifamily_name: str) -> float:
        """
        Total risk for a given instrument family ID.
        """
        if not self.rows:
            return 0
        return sum([x.risk for x in filter(lambda r: r.inst_family == ifamily_name, self.rows)])

    def total_for_risk_type(self, rtype: RiskType, currency: Currency) -> float:
        """
        Total risk for a given risk type.
        """
        if not self.rows:
            return 0

        def filt_f(r: RiskResultRow) -> bool:
            return r.risk_type == rtype and r.risk_currency == currency

        return sum(x.risk for x in filter(filt_f, self.rows))


def calculate_market_risk(
    pricers: List[Pricer],
    filter_instrument: Optional[InstrumentFilter] = None,
    remove_zero_sens: bool = False,
    in_place_bumps: bool = False,
) -> RiskResult:
    """
    Calculate sensitivities to each instrument in the market,
    optionally filtering instuments using provided predicate filter_instrument.

    in_place_bumps can be used to select between two methodologies:
    if false, MarketView object will be created where an associated instrument is replaced,
    and all affected curves are rebuilt from scratch;
    if true, QuantLib's relinkable quotes will be adjusted in place without
    creating new instruments or MarketView objects. This approach can often lead to
    better performance but may not always be appropriate, for example curves
    will not recalibrate back to identical points after quotes are reset so
    valuations will change slightly after risk calculation.
    Before choosing in_place_bumps=True verify the results against full rebuild method.
    """
    if in_place_bumps:
        return calculate_market_risk_in_place(pricers, filter_instrument, remove_zero_sens)
    else:
        return calculate_market_risk_full_rebuild(pricers, filter_instrument, remove_zero_sens)


def calculate_market_risk_in_place(
    pricers: List[Pricer],
    filter_instrument,
    remove_zero_sens,
) -> RiskResult:
    """
    Calculate sensitivities to each instrument in the market,
    optionally filtering by currencies.
    """
    results = RiskResult()
    if not pricers:
        return results
    market: MarketView = pricers[0].market

    for _, inst in market.get_instrument_map().items():
        if filter_instrument is not None and not filter_instrument.matches(inst):
            continue
        base_values = defaultdict(float)
        for p in pricers:
            for ccy_results in p.calculate(Metric.RISK_VALUE):
                vccy, ccy_value = ccy_results
                base_values[vccy] += ccy_value

        old_inst_quote = inst.quote
        bump_size = inst.get_family().get_default_bump()
        new_inst_quote = inst.get_family().bump_quote(inst.quote, bump_size)
        inst.set_quote(new_inst_quote)

        bump_values = defaultdict(float)
        for ipricer in pricers:
            for ccy_results in ipricer.calculate(Metric.RISK_VALUE):
                vccy, ccy_value = ccy_results
                bump_values[vccy] += ccy_value

        inst.set_quote(old_inst_quote)
        for iccy, ibase_value in base_values.items():
            sens = (bump_values[iccy] - ibase_value) / bump_size
            if remove_zero_sens and abs(sens) < 1e-5:
                continue
            tenor_as_time = try_get_tenor_time(inst.get_inst_specifics())
            row = RiskResultRow(
                risk_currency=iccy,
                instrument=inst.name,
                inst_currency=inst.get_currency(),
                risk=sens,
                inst_family=inst.get_family().name,
                inst_specifics=str(inst.get_inst_specifics()),
                quote=inst.get_quote(),
                asset_class=inst.get_asset_class(),
                risk_type=inst.get_risk_type(),
                tenor_time=tenor_as_time,
            )
            results.rows.append(row)
    return results


def calculate_market_risk_full_rebuild(
    pricers: List[Pricer],
    filter_instrument,
    remove_zero_sens,
) -> RiskResult:
    """
    Calculate sensitivities to each instrument in the market,
    optionally filtering by currencies.
    """
    results = RiskResult()
    if not pricers:
        return results
    base_market: MarketView = pricers[0].market
    bump_markets = base_market.get_bumped_markets(filter_instrument)
    base_values = defaultdict(float)
    for p in pricers:
        for ccy_results in p.calculate(Metric.RISK_VALUE):
            vccy, ccy_value = ccy_results
            base_values[vccy] += ccy_value
    for imarket_bump_info in bump_markets:
        bump_values = defaultdict(float)
        for ipricer in pricers:
            bump_pricer = ipricer.new_pricer_for_market(imarket_bump_info.market)
            for ccy_results in bump_pricer.calculate(Metric.RISK_VALUE):
                vccy, ccy_value = ccy_results
                bump_values[vccy] += ccy_value
        for iccy, ibase_value in base_values.items():
            sens = (bump_values[iccy] - ibase_value) / imarket_bump_info.bump_size
            instr = base_market.get_instrument(imarket_bump_info.instrument.name)
            if remove_zero_sens and abs(sens) < 1e-5:
                continue
            tenor_as_time = try_get_tenor_time(instr.get_inst_specifics())
            row = RiskResultRow(
                risk_currency=iccy,
                instrument=instr.name,
                inst_currency=instr.get_currency(),
                risk=sens,
                inst_family=instr.get_family().name,
                inst_specifics=str(instr.get_inst_specifics()),
                quote=instr.get_quote(),
                asset_class=instr.get_asset_class(),
                risk_type=instr.get_risk_type(),
                tenor_time=tenor_as_time,
            )
            results.rows.append(row)
    return results
