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

    name: str
    exchange: str
    contract_symbol: str

    def model_post_init(self, __context: Any) -> None:
        self._inst_meta = InstrumentFamilyMeta(
            currency=self.index.currency,
            risk_type=RiskType.RATE,
            asset_class=AssetClass.RATE,
        )

    def get_meta(self) -> InstrumentFamilyMeta:
        return self._inst_meta

    def get_name(self) -> str:
        return self.name

    def get_underlying_indices(self) -> List[Index]:
        return [self.index]

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
        contract_type = lookup_contract_type(self.exchange, self.contract_symbol)
        series = futures_symbol_to_month_start(term)
        return ql.OvernightIndexFutureRateHelper(
            quote_handle,  # QuoteHandle price,
            contract_type.accrual_start_date(series).to_ql(),  # Date valueDate,
            contract_type.accrual_end_date(series).to_ql(),  # Date maturityDate,
            self.index.get_ql_index(),  # ext::shared_ptr< OvernightIndex > const & index,
            ql.QuoteHandle(),  # QuoteHandle convexityAdjustment=Handle< Quote >(),
            self.averaging.to_ql(),  # RateAveraging::Type averagingMethod=Compound
        )
