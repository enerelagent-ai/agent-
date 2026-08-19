from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class InvestmentReproducibility(BaseModel):
    calculated_at: datetime
    comparison_group: str
    n_sale: int
    n_rent: int
    median_sale_price: float
    median_rent_price: float
    formula_version: str


class DistrictInvestmentSummary(BaseModel):
    district: str
    n_sale: int
    n_rent: int
    avg_sale_price: float
    min_sale_price: float
    median_sale_price: float
    max_sale_price: float
    avg_price_per_sqm: float | None
    gross_rental_yield_pct: float
    roi_pct: float
    investment_score: float
    confidence_tier: Literal["high", "medium", "low", "unavailable"]
    data_as_of: datetime
    room_coverage_pct: float
    area_coverage_pct: float
    price_guard_excluded_pct: float
    confidence_formula_version: str
    reproducibility: InvestmentReproducibility


class PriceTrendPoint(BaseModel):
    snapshot_date: date
    n_listings: int
    avg_price: float | None
    avg_price_per_sqm: float | None


class ListingTypeCount(BaseModel):
    bucket: str
    listing_type: str
    n: int


class MonthlyDelistingPoint(BaseModel):
    month: date
    listing_type: str
    district: str | None
    n_delisted: int


class DealAlertItem(BaseModel):
    id: int
    title: str
    source_url: str
    price: float | None
    district: str | None
    complex_name: str | None
    scraped_at: datetime
    deal_pct: float


class DealAlertFeed(BaseModel):
    items: list[DealAlertItem]
    unseen_count: int
    last_seen_at: datetime


class NotificationReadState(BaseModel):
    last_seen_at: datetime


class ComplexPriceSummary(BaseModel):
    complex_id: int
    complex_name: str
    listing_type: str
    property_type: str
    n_listings: int
    avg_price: float
    median_price: float
    avg_price_per_sqm: float | None
    median_price_per_sqm: float | None
    n_with_price_per_sqm: int


class ComplexOption(BaseModel):
    id: int
    canonical_name: str


class ComplexReviewItem(BaseModel):
    listing_id: int
    complex_id: int
    complex_name: str
    matched_alias: str | None
    relation: Literal["unit", "landmark", "unknown"]
    confidence: float
    evidence_text: str
    district: str | None
    address: str | None
    source_url: str
    review_reason: str | None
    can_approve: bool
    approval_block_reason: str | None
    detected_at: datetime


class ComplexReviewQueue(BaseModel):
    items: list[ComplexReviewItem]
    total: int
    pending_unit: int
    pending_landmark: int
    limit: int
    offset: int


class ComplexReviewDecision(BaseModel):
    decision: Literal["approve", "reject"]
    note: str | None = None


class ComplexReviewResult(BaseModel):
    listing_id: int
    complex_id: int
    review_status: Literal["approved", "rejected"]
    complex_id_after: int | None


class TodaysOpportunity(BaseModel):
    # No investment_score/roi_pct here on purpose -- see
    # analytics.calculations.todays_opportunity's docstring. Only the
    # individually-labeled real component metrics a reader can check
    # against the district table themselves.
    district: str
    n_sale: int
    n_rent: int
    avg_sale_price: float
    avg_price_per_sqm: float | None
    gross_rental_yield_pct: float
    # None when the district's own comparable groups (deal_percentages(),
    # grouped by district+rooms+listing_type) are all below
    # MIN_COMPARABLE_GROUP_SIZE -- a stricter, independent gate from the
    # n_sale/n_rent above, so this can be unavailable even when those
    # aren't. n_deals_analyzed is always present so a caller can tell "zero
    # comparables" apart from "no field returned".
    top_deal_pct: float | None
    n_deals_analyzed: int
    last_scraped_at: datetime
    confidence_tier: Literal["high", "medium", "low", "unavailable"]
    data_as_of: datetime
    room_coverage_pct: float
    area_coverage_pct: float
    price_guard_excluded_pct: float
    confidence_formula_version: str
    reproducibility: InvestmentReproducibility
