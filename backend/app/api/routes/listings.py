from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func

from analytics.matches import superseded_listing_ids_conn
from app.api.deps import DbSession
from app.config import settings
from app.models.listing import Listing
from app.schemas.listing import ListingFacets, ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])


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
    listing = db.get(Listing, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing
