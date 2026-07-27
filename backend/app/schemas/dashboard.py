from pydantic import BaseModel


class DistrictInvestmentSummary(BaseModel):
    district: str
    n_sale: int
    n_rent: int
    avg_sale_price: float
    gross_rental_yield_pct: float
    roi_pct: float
    investment_score: float
