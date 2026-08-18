import base64
import binascii
import json
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func, or_

from analytics.matches import superseded_listing_ids_conn
from app.api.deps import DbSession
from app.config import settings
from app.models.listing import Complex, Listing
from app.schemas.listing import ListingFacets, ListingOut, MarketplaceListingPage

router = APIRouter(prefix="/listings", tags=["listings"])


def _encode_cursor(scraped_at: datetime, listing_id: int) -> str:
    payload = json.dumps(
        [scraped_at.isoformat(), listing_id], separators=(",", ":")
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def _decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        padding = "=" * (-len(cursor) % 4)
        payload = json.loads(base64.urlsafe_b64decode(cursor + padding))
        if not isinstance(payload, list) or len(payload) != 2:
            raise ValueError
        scraped_at = datetime.fromisoformat(payload[0])
        listing_id = payload[1]
        if scraped_at.tzinfo is None or not isinstance(listing_id, int):
            raise ValueError
        return scraped_at, listing_id
    except (ValueError, TypeError, binascii.Error, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail="Invalid marketplace cursor") from exc


@router.get("/facets", response_model=ListingFacets)
def listing_facets(
    db: DbSession,
    listing_type: Literal["sale", "rent"] = Query(...),
) -> dict:
    """Filter metadata for one marketplace transaction type.

    Counts use the same publication boundary as marketplace browse: active
    listings with auto-resolved duplicate copies removed. Negotiable-price
    placeholders remain in category counts but cannot define a price range.
    """
    excluded_ids = superseded_listing_ids_conn(settings.database_url)

    def active_query(*columns):
        return db.query(*columns).filter(
            Listing.is_active.is_(True),
            Listing.listing_type == listing_type,
            Listing.id.notin_(excluded_ids),
        )

    total = active_query(func.count(Listing.id)).scalar() or 0
    district_rows = (
        active_query(Listing.district, func.count(Listing.id))
        .filter(Listing.district.is_not(None), Listing.district != "")
        .group_by(Listing.district)
        .order_by(func.count(Listing.id).desc(), Listing.district.asc())
        .all()
    )
    property_type_rows = (
        active_query(Listing.property_type, func.count(Listing.id))
        .filter(Listing.property_type.is_not(None), Listing.property_type != "")
        .group_by(Listing.property_type)
        .order_by(func.count(Listing.id).desc(), Listing.property_type.asc())
        .all()
    )
    room_rows = (
        active_query(Listing.rooms, func.count(Listing.id))
        .filter(Listing.rooms.is_not(None), Listing.rooms > 0)
        .group_by(Listing.rooms)
        .order_by(Listing.rooms.asc())
        .all()
    )
    price_min, price_max, price_count = (
        active_query(
            func.min(Listing.price),
            func.max(Listing.price),
            func.count(Listing.price),
        )
        .filter(
            Listing.price.is_not(None),
            Listing.price > 0,
            Listing.price_negotiable.is_not(True),
        )
        .one()
    )

    return {
        "listing_type": listing_type,
        "total": total,
        "districts": [
            {"value": value, "count": count} for value, count in district_rows
        ],
        "property_types": [
            {"value": value, "count": count}
            for value, count in property_type_rows
        ],
        "rooms": [{"value": value, "count": count} for value, count in room_rows],
        "price": {
            "min": float(price_min) if price_min is not None else None,
            "max": float(price_max) if price_max is not None else None,
            "count": price_count,
        },
    }


@router.get("/search", response_model=MarketplaceListingPage)
def search_marketplace_listings(
    db: DbSession,
    listing_type: Literal["sale", "rent"] = Query(...),
    district: str | None = Query(None),
    property_type: str | None = Query(None),
    rooms: int | None = Query(None, ge=1),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    cursor: str | None = Query(None),
    limit: int = Query(24, ge=1, le=100),
) -> dict:
    """Active canonical marketplace browse using stable keyset pagination."""
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price cannot exceed max_price")
    decoded_cursor = _decode_cursor(cursor) if cursor is not None else None

    excluded_ids = superseded_listing_ids_conn(settings.database_url)
    query = db.query(Listing).filter(
        Listing.is_active.is_(True),
        Listing.listing_type == listing_type,
        Listing.id.notin_(excluded_ids),
    )
    if district is not None:
        query = query.filter(Listing.district == district)
    if property_type is not None:
        query = query.filter(Listing.property_type == property_type)
    if rooms is not None:
        query = query.filter(Listing.rooms == rooms)
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    if decoded_cursor is not None:
        cursor_time, cursor_id = decoded_cursor
        query = query.filter(
            or_(
                Listing.scraped_at < cursor_time,
                and_(
                    Listing.scraped_at == cursor_time,
                    Listing.id < cursor_id,
                ),
            )
        )

    rows = (
        query.order_by(Listing.scraped_at.desc(), Listing.id.desc())
        .limit(limit + 1)
        .all()
    )
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = (
        _encode_cursor(items[-1].scraped_at, items[-1].id)
        if has_more and items
        else None
    )
    return {"items": items, "next_cursor": next_cursor, "has_more": has_more}


@router.get("", response_model=list[ListingOut])
def list_listings(
    db: DbSession,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[Listing]:
    # id as a tiebreaker: scraped_at alone ties across a batch insert (many
    # rows share the exact timestamp), and Postgres doesn't guarantee a
    # stable order for ties across separate queries -- offset pages could
    # overlap or skip rows. Same fix already applied to /dashboard/listings
    # (see dashboard.py) for the same reason.
    return (
        db.query(Listing)
        .order_by(Listing.scraped_at.desc(), Listing.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: DbSession) -> Listing:
    excluded_ids = superseded_listing_ids_conn(settings.database_url)
    listing = (
        db.query(Listing)
        .filter(
            Listing.id == listing_id,
            Listing.is_active.is_(True),
            Listing.id.notin_(excluded_ids),
        )
        .one_or_none()
    )
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    listing.complex_name = (
        db.query(Complex.canonical_name)
        .filter(Complex.id == listing.complex_id)
        .scalar()
        if listing.complex_id is not None
        else None
    )
    return listing
