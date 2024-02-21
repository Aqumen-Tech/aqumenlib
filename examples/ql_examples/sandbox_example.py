import QuantLib as ql

prevCouponDate = ql.Date(6, 9, 2023)
settlementDate = ql.Date(16, 2, 2024)
maturityDate = ql.Date(6, 3, 2024)
yld = 0.05437768
coupon = 0.06215
dc = ql.Actual365Fixed()
frac_ai = dc.yearFraction(prevCouponDate, settlementDate, prevCouponDate, maturityDate)
frac_y = dc.yearFraction(settlementDate, maturityDate, prevCouponDate, maturityDate)
dp_simple = 100.0 * (1.0 + coupon / 2) / (1 + yld * frac_y)
ai = 100 * coupon * frac_ai
cp_s = dp_simple - ai
print(f"clean price simple {cp_s}")
