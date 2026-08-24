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


class PublicComplexSummary(BaseModel):
    source_slug: str
    source_url: str
    name: str
    district: str | None
    median_sale_price_per_sqm: float | None
    active_listings: int
    lat: float | None
    lng: float | None
    photo_url: str | None
    has_contour: bool
    location_kind: str | None
    data_as_of: str


class PublicComplexMapData(BaseModel):
    profiles: list[PublicComplexSummary]
    contours: dict[str, list[list[list[float]]]]


class PublicAffordabilitySnapshot(BaseModel):
    source_url: str
    data_as_of: str
    districts: list[str]
    listings: list[list[float]]
    rules: dict
