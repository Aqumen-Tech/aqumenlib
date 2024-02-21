# Copyright AQUMEN TECHNOLOGY SOLUTIONS LTD 2023-2024

"""
BondPricer class
"""
from typing import Any, Optional
import pydantic
import QuantLib as ql

from aqumenlib import Date, MarketView, Pricer, QuoteConvention, Metric, TradeInfo
from aqumenlib import market_util
from aqumenlib.index import RateIndex, InflationIndex
from aqumenlib.cashflow import Cashflow, Cashflows
from aqumenlib.products.bond import Bond


class BondPricer(Pricer, pydantic.BaseModel):
    """
    Pricer for bonds
    """

    bond: Bond
    market: MarketView
    quote: float
    quote_convention: QuoteConvention
    trade_info: TradeInfo = TradeInfo()

    def model_post_init(self, __context: Any) -> None:
        self._discount_curve = None
        self._ql_bond = None
        self._quote_as_dirty_price = None
        self.set_market(self.market)

    def get_market(self) -> "MarketView":
        return self.market

    def set_market(self, market_model: MarketView):
        self.market: MarketView = market_model
        self.market.ql_set_pricing_date()
        self._discount_curve = self.market.get_discounting_curve(self.bond.bond_type.currency, self.trade_info.csa_id)
        df_term_structure = ql.RelinkableYieldTermStructureHandle()
        df_term_structure.linkTo(self._discount_curve.get_ql_curve())
        engine = ql.DiscountingBondEngine(df_term_structure)

        if self.bond.coupon is None and self.bond.bond_type.index is None:
            self._ql_bond = ql.ZeroCouponBond(
                self.bond.bond_type.settlement_delay,
                self.bond.bond_type.calendar,
                100.0,  #  faceAmount,
                self.bond.maturity.to_ql(),  # Dte maturityDate,
                self.bond.bond_type.payment_adjust.value,
                100.0,  # redemption,
                # issueDate=Date()
            )
        elif self.bond.bond_type.index is None:
            self._ql_bond = ql.FixedRateBond(
                self.bond.bond_type.settlement_delay,
                100.0,  # faceAmount
                self.bond._ql_bond_schedule,
                ql.DoubleVector(1, self.bond.coupon),
                self.bond.bond_type.ql_day_count(),  # paymentDayCounter
                self.bond.bond_type.payment_adjust.value,
                100.0,  # redemption percentage
                ql.Date(),  # issueDate = Date()
                self.bond.bond_type.calendar.to_ql(),  # paymentCalendar = Calendar()
                # exCouponPeriod=Period()
                # exCouponCalendar=Calendar()
                # exCouponConvention=Unadjusted
                # exCouponEndOfMonth=False
            )
        elif self.bond.bond_type.index != None and isinstance(self.bond.bond_type.index, RateIndex):
            ql_index = market_util.get_modeled_ql_rate_index(self.market, self.bond.bond_type.index)
            self._ql_bond = ql.FloatingRateBond(
                self.bond.bond_type.settlement_delay,
                100.0,
                self.bond._ql_bond_schedule,
                ql_index,
                self.bond.bond_type.ql_day_count(),
                self.bond.bond_type.payment_adjust.value,
                self.bond.bond_type.index.days_to_settle,  # fixingDays
                ql.DoubleVector(1, 1.0),  # Gearings
                ql.DoubleVector(1, self.bond.coupon),  # Spreads
                ql.DoubleVector(),  # Caps
                ql.DoubleVector(),  # Floors
                False,  # Fixing in arrears
                100.0,  # redemption
                # issueDate=Date(),
                # exCouponPeriod=Period(),
                # exCouponCalendar=Calendar(),
                # exCouponConvention=Unadjusted,
                # exCouponEndOfMonth=False
            )
        elif self.bond.bond_type.index is not None and isinstance(self.bond.bond_type.index, InflationIndex):
            ql_index = market_util.get_modeled_ql_inflation_index(self.market, self.bond.bond_type.index)
            self._ql_bond = ql.CPIBond(
                self.bond.bond_type.settlement_delay,  # Natural settlementDays,
                100.0,  # Real faceAmount,
                True,  # bool growthOnly, - i.e. deflation does not reduce principal
                self.bond.inflation_base,  # Real baseCPI,
                self.bond.inflation_lag.to_ql(),  # const Period& observationLag,
                ql_index,  # ext::shared_ptr<ZeroInflationIndex> cpiIndex,
                ql.CPI.Flat,  # CPI::InterpolationType observationInterpolation,
                self.bond._ql_bond_schedule,  # const Schedule& schedule,
                ql.DoubleVector(1, self.bond.coupon),  # const std::vector<Rate>& coupons,
                self.bond.bond_type.day_count_ai.to_ql(),  # const DayCounter& accrualDayCounter,
                self.bond.bond_type.payment_adjust.value,  #  paymentConvention = ModifiedFollowing,
                ql.Date(),  # const Date& issueDate = Date(),
                self.bond.bond_type.calendar.to_ql(),  # const Calendar& paymentCalendar = Calendar(),
                # const Period& exCouponPeriod = Period(),
                # const Calendar& exCouponCalendar = Calendar(),
                # BusinessDayConvention exCouponConvention = Unadjusted,
                # bool exCouponEndOfMonth = false
            )
        else:
            raise RuntimeError("Could not determine bond type for the pricer from given parameters")
        self._ql_bond.setPricingEngine(engine)
        match self.quote_convention:
            case QuoteConvention.Yield:
                self._quote_as_dirty_price = self.yield_to_price(self.quote) + self.accrued_interest()
            case QuoteConvention.CleanPrice:
                self._quote_as_dirty_price = self.quote + self.accrued_interest()
            case QuoteConvention.DirtyPrice:
                self._quote_as_dirty_price = self.quote
            case _:
                raise KeyError(f"Unsupported quote convention for the bond: {self.quote_convention.name}")

    def get_name(self):
        return self.bond.name

    def calculate(self, metric: Metric) -> Any:
        self.market.ql_set_pricing_date()
        match metric:
            case Metric.NATIVE_MARKET_VALUE:
                return self.market_value()
            case Metric.NATIVE_MODEL_VALUE:
                return self.model_value()
            case Metric.VALUE | Metric.MARKET_VALUE:
                return {self.bond.bond_type.currency: self.market_value()}
            case Metric.MODEL_VALUE | Metric.RISK_VALUE:
                return {self.bond.bond_type.currency: self.model_value()}
            case Metric.REPORTING_VALUE | Metric.REPORTING_MARKET_VALUE:
                fx = self.market.get_spot_FX(
                    self.get_pricer_settings().reporting_currency,
                    self.bond.bond_type.currency,
                )
                return self.market_value() / fx
            case Metric.REPORTING_MODEL_VALUE:
                fx = self.market.get_spot_FX(
                    self.get_pricer_settings().reporting_currency,
                    self.bond.bond_type.currency,
                )
                return self.model_value() / fx
            case Metric.CURRENCY:
                return self.bond.bond_type.currency
            case Metric.IRR:
                return self.irr()
            case Metric.YIELD:
                return self.standard_yield()
            case Metric.DURATION:
                return self.duration_modified()
            case Metric.DURATION_MACAULAY:
                return self.duration_macaulay()
            case Metric.CONVEXITY:
                return self.convexity()
            case Metric.ZSPREAD:
                return self.zspread()
            case Metric.CASHFLOWS:
                dt = self.market.pricing_date.to_ql()
                qcs = filter(lambda x: x.date() >= dt, self.ql_cashflows())
                flows = []
                for iflow in qcs:
                    flow = Cashflow(
                        currency=self.bond.bond_type.currency,
                        date=Date.from_ql(iflow.date()),
                        amount=iflow.amount() * self._amount_multiplier(),
                        notional=self.trade_info.amount,
                    )
                    flow.add_meta_from_ql(iflow)
                    flows.append(flow)
                return Cashflows(flows=flows)
            case _:
                return "N/A"

    def _amount_multiplier(self):
        direction = 1.0 if self.trade_info.is_receive else -1.0
        return self.trade_info.amount * direction / 100.0

    def settlement_date(self, trade_date: Optional[Date] = None) -> Date:
        """
        Settlement date of the bond trade (implied trade on market pricing date if trade date is not explicitly given).
        """
        d = trade_date.to_ql() if trade_date is not None else ql.Date()
        return Date.from_ql(self._ql_bond.settlementDate(d))

    def market_value(self) -> float:
        """
        Returns market value for the bond position, calculated by using market quote
        """
        return self._quote_as_dirty_price * self._amount_multiplier()

    def model_value(self) -> float:
        """
        Returns model value for the bond position, calculated by discounting cash flows
        """
        return self._ql_bond.NPV() * self._amount_multiplier()

    def value(self) -> float:
        """
        Shorthand for market_value()
        """
        return self.market_value()

    def clean_price_model(self) -> float:
        """
        Compute clean price based on discounted cashflows.
        """
        return self._ql_bond.cleanPrice()

    def dirty_price_model(self) -> float:
        """
        Compute dirty price based on discounted cashflows.
        """
        return self._ql_bond.dirtyPrice()

    def irr_model(self) -> float:
        """
        Compute bond yield as internal rate of return  based on discounted cashflows.
        """
        return self.price_to_yield(self._ql_bond.cleanPrice())

    def clean_price(self) -> float:
        """
        Compute clean price based on market quote.
        """
        return self._quote_as_dirty_price - self.accrued_interest()

    def dirty_price(self) -> float:
        """
        Compute dirty price based on market quote.
        """
        return self._quote_as_dirty_price

    def irr(self) -> float:
        """
        Compute bond yield as internal rate of return (IRR) based on market quote.
        IRR uses standard convention of ACT/365F day count and annual compounding.
        """
        return self._ql_bond.bondYield(
            self.clean_price(),
            ql.Actual365Fixed(),
            ql.Compounded,
            ql.Annual,
        )

    def standard_yield(self) -> float:
        """
        Compute standard bond yield based on market quote. Uses bond's day count and frequency.
        """
        return self.price_to_yield(self.clean_price())

    def accrued_interest(self) -> float:
        """
        Compute accrued interest normalized to 100 notional.
        """
        return self._ql_bond.accruedAmount()

    def price_to_yield(self, clean_price: float) -> float:
        """
        Conversion utility - calculates yield given clean price, normalized to 100 notional.
        """
        return self._ql_bond.bondYield(
            clean_price,
            self.bond.bond_type.ql_day_count(),
            ql.Compounded,
            self.bond.bond_type.frequency.value,
        )

    def yield_to_price(self, yield_quote: float) -> float:
        """
        Conversion utility - calculates clean price given yield, normalized to 100 notional.
        """
        return self._ql_bond.cleanPrice(
            yield_quote,
            self.bond.bond_type.ql_day_count(),
            ql.Compounded,
            self.bond.bond_type.frequency.value,
        )

    def duration_modified(self) -> float:
        """
        Compute modified duration using market quote.
        """
        return ql.BondFunctions.duration(
            self._ql_bond,
            self.standard_yield(),
            self.bond.bond_type.ql_day_count(),
            ql.Compounded,
            self.bond.bond_type.frequency.value,
            ql.Duration.Modified,
        )

    def duration_macaulay(self) -> float:
        """
        Compute Macaulay duration using market quote.
        """
        return ql.BondFunctions.duration(
            self._ql_bond,
            self.standard_yield(),
            self.bond.bond_type.ql_day_count(),
            ql.Compounded,
            self.bond.bond_type.frequency.value,
            ql.Duration.Macaulay,
        )

    def convexity(self) -> float:
        """
        Compute bond convexity using market quote.
        """
        return ql.BondFunctions.convexity(
            self._ql_bond,
            self.standard_yield(),
            self.bond.bond_type.ql_day_count(),
            ql.Compounded,
            self.bond.bond_type.frequency.value,
        )

    def zspread(self) -> float:
        """
        Compute bond zspread using market quote.
        """
        df_term_structure = ql.RelinkableYieldTermStructureHandle()
        df_term_structure.linkTo(self._discount_curve.get_ql_curve())
        return ql.BondFunctions.zSpread(
            self._ql_bond,
            self.clean_price(),
            self._discount_curve.get_ql_curve(),
            self.bond.bond_type.ql_day_count(),
            ql.Compounded,
            self.bond.bond_type.frequency.value,
        )

    def ql_cashflows(self):
        """
        QuantLib cashf flows
        """
        return self._ql_bond.cashflows()
