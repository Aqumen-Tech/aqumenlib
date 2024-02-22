# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
Interest Rate Future instruments to be used for calibration
"""
from typing import Any, Optional, List
from aqumenlib.instruments.future_contract import futures_symbol_to_month_start, lookup_contract_type
import pydantic
import QuantLib as ql
from aqumenlib import (
    RiskType,
    AssetClass,
    MarketView,
)
from aqumenlib.index import Index
from aqumenlib.instrument_family import InstrumentFamilyMeta
from aqumenlib.instruments.rate_family import RateInstrumentFamily


class OIFutureFamily(RateInstrumentFamily, pydantic.BaseModel):
    """
    Overnight Index Interest Rate Future instrument.
    """

    name: Optional[str] = None
    exchange: str
    contract_symbol: str

    def model_post_init(self, __context: Any) -> None:
        if not self.name:
            self.name = f"FUT-{self.exchange}-{self.contract_symbol}"
        self._contract_type = lookup_contract_type(self.exchange, self.contract_symbol)
        self._inst_meta = InstrumentFamilyMeta(
            currency=self._contract_type.get_index().currency,
            risk_type=RiskType.RATE,
            asset_class=AssetClass.RATE,
        )

    def specifics_input_process(self, specifics_input: Any) -> Any:
        """
        Family-specific input converter for instrument specifics.
        Normally it's just maturity, but it can be overwritten to handle other
        instrument conventions.
        """
        # most instruments use maturity code like 10Y for specifics, so let us
        # provide default implementation for those
        return specifics_input

    def get_meta(self) -> InstrumentFamilyMeta:
        return self._inst_meta

    def get_name(self) -> str:
        return self.name

    def get_underlying_indices(self) -> List[Index]:
        return [self.index]

    def bump_quote(self, old_quote: float, bump_size: float) -> float:
        """
        Calculate new quote given a bump that should apply to a relevant underlying metric.
        For example, if the instrument is a rate futures one where quote is presented as 100*(1-r)
        where r is underlying rate, then this method will be overwritten in
        the most derived instrument family to return q - bump_size*100
        """
        return old_quote - bump_size * 100

    def create_ql_instrument(
        self,
        market: "MarketView",
        quote_handle: ql.RelinkableQuoteHandle,
        term: str,  # for futures term should be series code e.g. Z21
        discounting_id: Optional[str] = None,
        target_curve: Optional["Curve"] = None,
    ):
        """
        Create QuantLib represenation of this instrument
        """
        series = futures_symbol_to_month_start(term)
        return ql.OvernightIndexFutureRateHelper(
            quote_handle,  # QuoteHandle price,
            self._contract_type.accrual_start_date(series).to_ql(),  # Date valueDate,
            self._contract_type.accrual_end_date(series).to_ql(),  # Date maturityDate,
            self._contract_type.get_index().get_ql_index(),  # ext::shared_ptr< OvernightIndex > const & index,
            ql.QuoteHandle(),  # QuoteHandle convexityAdjustment=Handle< Quote >(),
            self._contract_type.rate_averaging().to_ql(),  # RateAveraging::Type averagingMethod=Compound
        )
