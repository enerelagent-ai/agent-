from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.models.listing import Listing
from app.schemas.listing import ListingOut

router = APIRouter(prefix="/listings", tags=["listings"])


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
