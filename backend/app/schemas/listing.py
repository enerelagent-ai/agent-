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

    # From analytics.estimate_negotiable_price() — only ever set for
    # price_negotiable listings that also clear that function's own
    # comparability guards (see its docstring). estimate_basis is
    # 'area_based' or 'group_median_price'; estimated_price_per_sqm is only
    # set for the former.
    estimated_price: float | None = None
    estimated_price_per_sqm: float | None = None
    estimate_basis: str | None = None
