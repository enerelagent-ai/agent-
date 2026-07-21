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
    area_sqm: float | None
    price_per_sqm: float | None
    rooms: int | None
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
