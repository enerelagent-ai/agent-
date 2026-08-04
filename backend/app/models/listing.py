from datetime import datetime

from sqlalchemy import ARRAY, BigInteger, Boolean, Computed, DateTime, Double, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Listing(Base):
    """Mirrors the `listings` table defined in db/schema.sql."""

    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    source: Mapped[str] = mapped_column(String(20))
    source_url: Mapped[str] = mapped_column(Text)

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    # True when the source lists a placeholder alongside the price (e.g.
    # "170 ₮ Үнэ тохирно") -- that price is not real, see
    # analytics.estimate_negotiable_price().
    price_negotiable: Mapped[bool | None] = mapped_column(Boolean)
    area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2))
    # GENERATED ALWAYS AS (...) STORED in db/schema.sql -- Computed() (not
    # just a comment) is required so SQLAlchemy omits this from INSERT/UPDATE
    # statements; Postgres rejects any explicit value, even NULL, for a
    # generated column. The expression is a copy of schema.sql's for anyone
    # who ever runs Base.metadata.create_all() against this model (nothing
    # in this app does today -- migrations in db/ own the real schema).
    price_per_sqm: Mapped[float | None] = mapped_column(
        Numeric(14, 2),
        Computed("CASE WHEN area_sqm > 0 THEN ROUND(price / area_sqm, 2) ELSE NULL END", persisted=True),
    )

    rooms: Mapped[int | None] = mapped_column(SmallInteger)
    listing_type: Mapped[str | None] = mapped_column(Text)
    property_type: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str | None] = mapped_column(Text)
    address: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Double)
    lng: Mapped[float | None] = mapped_column(Double)

    contact_phone: Mapped[str | None] = mapped_column(Text)
    photo_urls: Mapped[list[str]] = mapped_column(ARRAY(Text))

    dedup_hash: Mapped[str] = mapped_column(Text)

    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
