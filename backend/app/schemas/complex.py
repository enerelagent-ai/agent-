from datetime import datetime

from pydantic import BaseModel


class ComplexIntelligenceSummary(BaseModel):
    id: int
    name: str
    district: str | None
    active_listings: int
    sale_listings: int
    rent_listings: int
    median_sale_price_per_sqm: float | None
    min_sale_price_per_sqm: float | None
    max_sale_price_per_sqm: float | None
    lat: float | None
    lng: float | None
    location_kind: str
    has_contour: bool
    data_as_of: datetime


class ComplexIntelligenceDetail(ComplexIntelligenceSummary):
    aliases: list[str]
    median_sale_price: float | None
    median_rent_price: float | None

