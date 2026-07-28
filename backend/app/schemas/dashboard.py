from datetime import date

from pydantic import BaseModel


class DistrictInvestmentSummary(BaseModel):
    district: str
    n_sale: int
    n_rent: int
    avg_sale_price: float
    avg_price_per_sqm: float | None
    gross_rental_yield_pct: float
    roi_pct: float
    investment_score: float


class PriceTrendPoint(BaseModel):
    snapshot_date: date
    n_listings: int
    avg_price: float | None
    avg_price_per_sqm: float | None


class ListingTypeCount(BaseModel):
    bucket: str
    listing_type: str
    n: int
