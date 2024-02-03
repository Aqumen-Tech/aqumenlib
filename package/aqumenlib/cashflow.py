# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Cashflow class
"""
from typing import Any, Optional, List
import pandas as pd
import pydantic

import QuantLib as ql
from aqumenlib import Currency, Date


class Cashflow(pydantic.BaseModel):
    """
    Representation of a single cashflow, with meta-data attached.
    """

    date: Date
    amount: float
    currency: Currency
    notional: Optional[float]
    index_name: Optional[str] = None
    fixing_date: Optional[Date] = None
    fixing: Optional[float] = None
    base_fixing: Optional[float] = None
    rate: Optional[float] = None
    accrual_start: Optional[Date] = None
    accrual_end: Optional[Date] = None
    ref_start: Optional[Date] = None
    ref_end: Optional[Date] = None
    # exdiv_date: Optional[Date] = None
    accrual_fraction: Optional[float] = None

    def to_dict(self):
        """
        Converts to a dictionary suitable for DataFrame construction
        """

        def opt_value(v):
            return v if v is not None else "N/A"

        def opt_date(v):
            return v.to_isostr() if v is not None else "N/A"

        dict_for_df = {}
        dict_for_df["Date"] = self.date.to_isostr()
        dict_for_df["Amount"] = self.amount
        dict_for_df["Currency"] = self.currency.name
        dict_for_df["Notional"] = opt_value(self.notional)
        dict_for_df["Rate"] = opt_value(self.rate)
        dict_for_df["Index"] = opt_value(self.index_name)
        dict_for_df["Accrual Start"] = opt_date(self.accrual_start)
        dict_for_df["Accrual End"] = opt_date(self.accrual_end)
        dict_for_df["Accrual Fraction"] = opt_value(self.accrual_fraction)
        dict_for_df["Ref Start"] = opt_date(self.ref_start)
        dict_for_df["Ref End"] = opt_date(self.ref_end)
        dict_for_df["Fix Date"] = opt_date(self.fixing_date)
        dict_for_df["Fixing"] = opt_value(self.fixing)
        dict_for_df["Base"] = opt_value(self.base_fixing)
        return dict_for_df

    def add_meta_from_ql(self, ql_flow: Any) -> None:
        """
        Add optional meta data from a QuantLib CashFlow object.
        """
        ind_flow = ql.as_indexed_cashflow(ql_flow)
        if ind_flow:
            self.notional = ind_flow.notional()
            self.index_name = ind_flow.index().name()
            self.fixing_date = Date.from_ql(ind_flow.fixingDate())
            self.fixing = ind_flow.indexFixing()
            self.base_fixing = ind_flow.baseFixing()
        cp_flow = ql.as_coupon(ql_flow)
        if cp_flow:
            self.rate = cp_flow.rate()
            self.accrual_start = Date.from_ql(cp_flow.accrualStartDate())
            self.accrual_end = Date.from_ql(cp_flow.accrualEndDate())
            self.ref_start = Date.from_ql(cp_flow.referencePeriodStart())
            self.ref_end = Date.from_ql(cp_flow.referencePeriodEnd())
            # self.exdiv_date = Date.from_ql(cp_flow.exCouponDate())
            self.accrual_fraction = cp_flow.accrualPeriod()


class Cashflows(pydantic.BaseModel):
    """
    Set of cashflows.
    """

    flows: List[Cashflow] = []

    def __str__(self) -> str:
        df = self.to_dataframe()
        df["Amount"] = df["Amount"].apply(lambda x: f"{x:,.2f}")
        return str(df.to_string(index=False))

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert results to a pandas dataframe.
        """
        if not self.flows:
            return pd.DataFrame()
        df_data = []
        for row in self.flows:
            df_data.append(row.to_dict())
        df = pd.DataFrame(df_data)
        df = df.sort_values(["Currency", "Date", "Notional"])
        return df
