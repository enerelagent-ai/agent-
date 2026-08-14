from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_url: str
    title: str
    description: str | None
    price: float | None
    price_negotiable: bool | None
    area_sqm: float | None
    price_per_sqm: float | None
    rooms: int | None
    floor: int | None
    total_floors: int | None
    complex_id: int | None
    complex_name: str | None = None
    listing_type: str | None
    property_type: str | None
    district: str | None
    address: str | None
    lat: float | None
    lng: float | None
    contact_phone: str | None
    photo_urls: list[str]
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime
    # dedup_hash is deliberately omitted — internal to dedup logic, not for API consumers.

    # From analytics.deal_percentages() — only ever set for apartments with
    # rooms in 1-4 (see deal_percentages' docstring for the exclusions).
    # Defaults to None so endpoints that don't attach these (e.g. plain
    # /listings) still validate: Pydantic falls back to the field default
    # when the attribute is absent from the source object entirely.
    deal_pct: float | None = None
    deal_status: str | None = None
    deal_reason: str | None = None
    n_comparable: int | None = None
    # Also from deal_percentages() — the group's own median price/m², so a
    # detail view can show "your price/m² vs the group's" as absolute
    # numbers, not just the derived deal_pct.
    group_median_price_per_sqm: float | None = None

    # Independent complex-level comparison. Its 20% notable threshold is
    # deliberately stricter than the district-level 10% threshold above.
    complex_deal_pct: float | None = None
    complex_deal_status: str | None = None
    complex_deal_reason: str | None = None
    complex_n_comparable: int | None = None
    complex_median_price_per_sqm: float | None = None

    # From analytics.estimate_negotiable_price() — only ever set for
    # price_negotiable listings that also clear that function's own
    # comparability guards (see its docstring). estimate_basis is
    # 'area_based' or 'group_median_price'; estimated_price_per_sqm is only
    # set for the former.
    estimated_price: float | None = None
    estimated_price_per_sqm: float | None = None
    estimate_basis: str | None = None

    # From analytics.rental_yield_by_district_rooms() (Week 5, unchanged) —
    # matched by (district, rooms) regardless of this listing's own
    # listing_type, since the bucket already reflects a sale/rent pairing.
    # None when no bucket matches (non-apartments, or no comparable rent-side
    # data for this district+room-count) — a detail view should say so
    # plainly rather than guessing. n_sale/n_rent are that bucket's sample
    # sizes, for judging how much to trust the figure.
    rental_yield_pct: float | None = None
    rental_yield_payback_years: float | None = None
    rental_yield_n_sale: int | None = None
    rental_yield_n_rent: int | None = None
