from analytics.calculations import investment_summary_by_district_conn
from analytics.matches import superseded_listing_ids_conn
from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.config import settings
from app.models.listing import Listing
from app.schemas.dashboard import DistrictInvestmentSummary
from app.schemas.listing import ListingOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/investment-summary", response_model=list[DistrictInvestmentSummary])
def investment_summary() -> list[dict]:
    return investment_summary_by_district_conn(settings.database_url)


@router.get("/listings", response_model=list[ListingOut])
def list_dashboard_listings(
    db: DbSession,
    district: str | None = Query(None),
    property_type: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[Listing]:
    """Filtered, paginated listing browse for the dashboard search/browse view.

    Superseded duplicate listings (matches.superseded_listing_ids — the
    >=0.80 auto-resolve tier, see analytics.matches) are excluded so a
    repost doesn't show up twice; there's no query param to turn this off,
    since nothing has asked for the raw including-duplicates view yet.

    Ordered by (scraped_at, id) rather than scraped_at alone: many rows
    share an identical scraped_at (batch inserts), and scraped_at-only
    ordering is not guaranteed stable across separate queries when there's
    a tie — verified against the real DB, where that made different pages
    return overlapping rows. id is unique, so the tiebreaker makes paging
    deterministic and gapless.
    """
    query = db.query(Listing).filter(Listing.id.notin_(superseded_listing_ids_conn(settings.database_url)))
    if district is not None:
        query = query.filter(Listing.district == district)
    if property_type is not None:
        query = query.filter(Listing.property_type == property_type)
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    return (
        query.order_by(Listing.scraped_at.desc(), Listing.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
