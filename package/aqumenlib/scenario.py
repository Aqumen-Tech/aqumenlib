# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Facilities for scenario analysis
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any, Iterable
import copy
import pandas as pd

import pydantic

from aqumenlib import (
    Currency,
    MarketView,
    Instrument,
    AssetClass,
    RiskType,
    QuoteBumpType,
    Pricer,
    Metric,
)
from aqumenlib.instrument import InstrumentFilter, try_get_tenor_time
from aqumenlib.namedobject import NamedObject


class ScenarioResultRow(pydantic.BaseModel):
    """
    Data row for scenario results.
    """

    pricer_name: str
    scenario_name: str
    value_type: Metric
    base_value: float
    scen_value: float
    change_abs: float = 0
    change_rel: float = 0

    def model_post_init(self, __context: Any) -> None:
        self.change_abs = self.scen_value - self.base_value
        if abs(self.base_value) != 0:
            self.change_rel = self.change_abs / self.base_value
        else:
            self.change_rel = "inf"

    def to_dict(self):
        """
        Converts this row to a dictionary suitable for DataFrame construction
        """
        dict_for_df = {}
        dict_for_df["Pricer"] = self.pricer_name
        dict_for_df["Scenario"] = self.scenario_name
        dict_for_df["Base Value"] = self.base_value
        dict_for_df["Scen Value"] = self.scen_value
        dict_for_df["Abs Diff"] = self.change_abs
        dict_for_df["Percent Diff"] = self.change_rel * 100.0
        dict_for_df["Metric"] = self.value_type.name
        return dict_for_df


class ScenarioResult(pydantic.BaseModel):
    """
    Data store for scenarios results - essentially a table stored as list of rows
    and convertible to pandas DataFrame
    """

    rows: List[ScenarioResultRow] = []

    def __str__(self) -> str:
        df = self.to_dataframe()
        for col in ["Base Value", "Scen Value", "Abs Diff"]:
            df[col] = df[col].apply(lambda x: f"{x:,.2f}")
        df["Percent Diff"] = df["Percent Diff"].round(2)
        return str(df.to_string(index=False))

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert results to a pandas DataFrame.
        """
        if not self.rows:
            return pd.DataFrame()
        df_data = []
        for row in self.rows:
            df_data.append(row.to_dict())
        df = pd.DataFrame(df_data)
        df = df.sort_values(["Pricer", "Scenario"])
        return df


class BaseQuoteAdjuster(ABC, pydantic.BaseModel):
    """
    Interface for classes that modify quotes in MarketView.
    """

    @abstractmethod
    def apply_adjustment(self, instrument: Instrument) -> Instrument:
        """
        Applies adjustment to a quote by constructing a new instrument
        with a quote adjusted from the original value.
        """


class SimpleQuoteAdjuster(BaseQuoteAdjuster, pydantic.BaseModel):
    """
    Encode the rule for adjusting or bumping a quote (e.g. for sensitivity or scenario calculations).
    """

    adjustment_type: QuoteBumpType
    adjustment_value: float

    def apply_adjustment(self, instrument: Instrument) -> Instrument:
        """
        Applies adjustment to a quote by constructing a new instrument
        with a quote adjusted from the original value.
        """
        new_inst_quote = instrument.quote
        match self.adjustment_type:
            case QuoteBumpType.RELATIVE:
                new_inst_quote += new_inst_quote * (1.0 + self.adjustment_value)
            case QuoteBumpType.ABSOLUTE:
                new_inst_quote += self.adjustment_value
            case QuoteBumpType.FIXED:
                new_inst_quote = self.adjustment_value
        new_inst = Instrument(name=instrument.name, inst_type=instrument.inst_type, quote=new_inst_quote)
        return new_inst


class TermStructureQuoteAdjuster(BaseQuoteAdjuster, pydantic.BaseModel):
    """
    Encode the rule for adjusting or bumping a quote based on a function of instrument's pillar time.
    """

    adjustment_type: QuoteBumpType
    adjustment_function: Any

    def apply_adjustment(self, instrument: Instrument) -> Instrument:
        """
        Applies adjustment to a quote by constructing a new instrument
        with a quote adjusted from the original value.
        """
        pillar_time = try_get_tenor_time(instrument.get_inst_specifics())
        if pillar_time is None:
            return instrument
        new_inst_quote = instrument.quote
        match self.adjustment_type:
            case QuoteBumpType.RELATIVE:
                new_inst_quote += new_inst_quote * (1.0 + self.adjustment_function(pillar_time))
            case QuoteBumpType.ABSOLUTE:
                new_inst_quote += self.adjustment_function(pillar_time)
            case QuoteBumpType.FIXED:
                new_inst_quote = self.adjustment_function(pillar_time)
        new_inst = Instrument(name=instrument.name, inst_type=instrument.inst_type, quote=new_inst_quote)
        return new_inst


class SelectedQuoteAdjuster(pydantic.BaseModel):
    """
    Combines quote adjuster object with a set of filtering criteria.
    """

    adjuster: BaseQuoteAdjuster
    filter_instrument: Optional[InstrumentFilter] = None

    def matches_instrument(self, instrument: Instrument) -> bool:
        """
        Returns true if an instrument matches the filters in this object.
        """
        if self.filter_instrument is not None:
            return self.filter_instrument.matches(instrument)
        return True


class Scenario(NamedObject):
    """
    Base class for any scenario.
    Scenario represents an ability to change the MarketView object in particular way.
    """

    @abstractmethod
    def create_market(self, market: MarketView) -> MarketView:
        """
        Generate a new MarketView object by applying this scenario to it
        """


class AdjustQuotesScenario(Scenario, pydantic.BaseModel):
    """
    Scenario representing changes to quotes of instruments that match filter criteria.
    """

    name: str
    instrument_adjusments: List[SelectedQuoteAdjuster]

    def get_name(self):
        return self.name

    def create_market(self, market: MarketView) -> MarketView:
        """
        Generate a new MarketView object by applying this scenario to it.
        """
        affected_instruments = []
        new_inst_dict = copy.copy(market.get_instrument_map())
        for adj in self.instrument_adjusments:
            for _, inst in market.get_instrument_map().items():
                if adj.matches_instrument(inst):
                    new_inst: Instrument = adj.adjuster.apply_adjustment(inst)
                    new_inst_dict[inst.name] = new_inst
                    affected_instruments.append(new_inst)
        new_market = market.new_market_for_instruments(affected_instruments)
        return new_market


@pydantic.validate_call
def create_adjust_quotes_scenario(
    name: str,
    adjustment_type: QuoteBumpType,
    adjustment_value: float,
    filter_instrument: Optional[str] = None,
    filter_instrument_family: Optional[str] = None,
    filter_currency: Optional[Currency] = None,
    filter_risk_type: Optional[RiskType] = None,
    filter_asset_class: Optional[AssetClass] = None,
):
    """
    Construct a scenario object that adjusts quotes on instruments matching the criteria.
    """
    adjuster = SimpleQuoteAdjuster(
        adjustment_type=adjustment_type,
        adjustment_value=adjustment_value,
    )
    filt = InstrumentFilter(
        filter_instrument_name=[filter_instrument] if filter_instrument else None,
        filter_instrument_family=[filter_instrument_family] if filter_instrument_family else None,
        filter_currency=[filter_currency] if filter_currency else None,
        filter_risk_type=[filter_risk_type] if filter_risk_type else None,
        filter_asset_class=[filter_asset_class] if filter_asset_class else None,
    )
    filtered_adjuster = SelectedQuoteAdjuster(
        adjuster=adjuster,
        filter_instrument=filt,
    )
    scenario = AdjustQuotesScenario(name=name, instrument_adjusments=[filtered_adjuster])
    return scenario


@pydantic.validate_call
def create_curve_shape_scenario(
    name: str,
    adjustment_type: QuoteBumpType,
    adjustment_function: Any,
    filter_instrument_family: Optional[str] = None,
    filter_currency: Optional[Currency] = None,
    filter_risk_type: Optional[RiskType] = None,
):
    """
    Construct a scenario object that changes shape (term structure) of a curve
    by applying a user-provided function to produce shift values based on instruments' pillar time
    """
    adjuster = TermStructureQuoteAdjuster(
        adjustment_type=adjustment_type,
        adjustment_function=adjustment_function,
    )
    filt = InstrumentFilter(
        filter_instrument_family=[filter_instrument_family] if filter_instrument_family else None,
        filter_currency=[filter_currency] if filter_currency else None,
        filter_risk_type=[filter_risk_type] if filter_risk_type else None,
    )
    filtered_adjuster = SelectedQuoteAdjuster(
        adjuster=adjuster,
        filter_instrument=filt,
    )
    scenario = AdjustQuotesScenario(name=name, instrument_adjusments=[filtered_adjuster])
    return scenario


def calculate_scenario_impact(
    scenario: Scenario,
    pricer: Pricer,
    metric: Metric,
) -> ScenarioResult:
    """
    Given a  pricer and a valuation metric, return a ScenarioResult
    object that will contain a single row of results.

    """
    market = pricer.get_market()
    scenario_market = scenario.create_market(market)
    scenario_pricer = pricer.new_pricer_for_market(scenario_market)

    base_value = pricer.calculate(metric)
    new_value = scenario_pricer.calculate(metric)
    result = ScenarioResultRow(
        pricer_name=pricer.get_name(),
        scenario_name=scenario.get_name(),
        base_value=base_value,
        scen_value=new_value,
        value_type=metric,
    )
    return ScenarioResult(rows=[result])


@pydantic.validate_call
def combine_scenario_results(scenarios: Iterable[ScenarioResult]) -> ScenarioResult:
    """
    Combine multiple scenario results into a single object.
    """
    new_rows = []
    for iscen in scenarios:
        new_rows.extend(iscen.rows)
    return ScenarioResult(rows=new_rows)
