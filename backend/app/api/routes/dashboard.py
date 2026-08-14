from typing import Literal

from analytics.calculations import (
    complex_average_price_conn,
    complex_deal_percentages_conn,
    deal_percentages_conn,
    estimate_negotiable_price_conn,
    investment_summary_by_district_conn,
    listing_counts_by_property_type_conn,
    price_trend_conn,
    rental_yield_by_district_rooms_conn,
    todays_opportunity_conn,
)
from analytics.matches import superseded_listing_ids_conn
from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.config import settings
from app.models.listing import Listing
from app.schemas.dashboard import (
    DistrictInvestmentSummary,
    ComplexPriceSummary,
    ListingTypeCount,
    PriceTrendPoint,
    TodaysOpportunity,
)
from app.schemas.listing import ListingOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/investment-summary", response_model=list[DistrictInvestmentSummary])
def investment_summary() -> list[dict]:
    return investment_summary_by_district_conn(settings.database_url)


@router.get("/todays-opportunity", response_model=TodaysOpportunity | None)
def todays_opportunity() -> dict | None:
    """"Best available opportunity today" headline, or None when no
    district clears investment_summary_by_district's own data-sufficiency
    threshold yet (a thin or freshly-seeded DB) -- callers must render
    that as "not available", never as a placeholder. See
    analytics.calculations.todays_opportunity for the full derivation.
    """
    return todays_opportunity_conn(settings.database_url)


@router.get("/price-trend", response_model=list[PriceTrendPoint])
def price_trend(
    listing_type: str = Query("sale"),
    property_type: str = Query("Орон сууц зарна"),
) -> list[dict]:
    """Overall price trend for one (listing_type, property_type) slice, one
    point per price_history snapshot. Defaults to sale-side apartments — see
    analytics.calculations.price_trend for why. Only ever has as many points
    as snapshot_market_prices() has been run; today that's a single point.
    """
    return price_trend_conn(settings.database_url, listing_type, property_type)


@router.get("/listing-counts-by-type", response_model=list[ListingTypeCount])
def listing_counts_by_type() -> list[dict]:
    return listing_counts_by_property_type_conn(settings.database_url)


@router.get("/complex-prices", response_model=list[ComplexPriceSummary])
def complex_prices(complex_id: int | None = Query(None, ge=1)) -> list[dict]:
    """Current canonical price statistics, optionally for one complex."""
    return complex_average_price_conn(settings.database_url, complex_id)


def _attach_computed_fields(
    listing: Listing,
    deal: dict | None,
    complex_deal: dict | None,
    estimate: dict | None,
    yield_info: dict | None,
) -> Listing:
    listing.deal_pct = float(deal["deal_pct"]) if deal else None
    listing.deal_status = deal["deal_status"] if deal else None
    listing.deal_reason = deal["deal_reason"] if deal else None
    listing.n_comparable = deal["n_comparable"] if deal else None
    listing.group_median_price_per_sqm = float(deal["group_median_price_per_sqm"]) if deal else None
    listing.complex_name = complex_deal["complex_name"] if complex_deal else None
    listing.complex_deal_pct = float(complex_deal["complex_deal_pct"]) if complex_deal else None
    listing.complex_deal_status = complex_deal["complex_deal_status"] if complex_deal else None
    listing.complex_deal_reason = complex_deal["complex_deal_reason"] if complex_deal else None
    listing.complex_n_comparable = complex_deal["complex_n_comparable"] if complex_deal else None
    listing.complex_median_price_per_sqm = (
        float(complex_deal["complex_median_price_per_sqm"])
        if complex_deal
        else None
    )
    listing.estimated_price = float(estimate["estimated_price"]) if estimate else None
    listing.estimated_price_per_sqm = (
        float(estimate["estimated_price_per_sqm"])
        if estimate and estimate["estimated_price_per_sqm"] is not None
        else None
    )
    listing.estimate_basis = estimate["estimate_basis"] if estimate else None
    listing.rental_yield_pct = float(yield_info["gross_rental_yield_pct"]) if yield_info else None
    listing.rental_yield_payback_years = float(yield_info["payback_years"]) if yield_info else None
    listing.rental_yield_n_sale = yield_info["n_sale"] if yield_info else None
    listing.rental_yield_n_rent = yield_info["n_rent"] if yield_info else None
    return listing


@router.get("/listings", response_model=list[ListingOut])
def list_dashboard_listings(
    db: DbSession,
    district: str | None = Query(None),
    property_type: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    sort_by: Literal["recent", "deal_pct"] = Query("recent"),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
) -> list[Listing]:
    """Filtered, paginated listing browse for the dashboard search/browse view.

    Superseded duplicate listings (matches.superseded_listing_ids — the
    >=0.80 auto-resolve tier, see analytics.matches) are excluded so a
    repost doesn't show up twice; there's no query param to turn this off,
    since nothing has asked for the raw including-duplicates view yet.

    Every listing carries the independent district-level
    deal_pct/deal_status/deal_reason/n_comparable fields from
    analytics.deal_percentages(), plus complex_deal_pct/status/reason/
    n_comparable and complex_name from complex_deal_percentages(). The
    district signal uses a 10% notable threshold; the tighter complex signal
    uses 20%. Either comparison can be None while the other is available.

    District fields are None for
    listings deal_percentages() doesn't cover (non-apartments, apartments
    below its area floor, or the open-ended "5+ өрөө" bucket; see that
    function's docstring for the full list of exclusions and why each
    exists). deal_status is 'top_deal', 'needs_review' (an extreme enough
    deviation that a wrong comparison group is a more likely explanation
    than a genuine bargain — deal_reason then explains why), 'not_notable',
    or None when not applicable.

    sort_by="deal_pct" ranks best-deal-first using that same precomputed,
    already-sorted dataset, filtered down to listings matching the other
    params (deal_percentages() only tracks id/district/property_type/price,
    not every listings column, so filtering happens here rather than in
    that function) before the matching page is fetched from the DB and
    reordered to match — the ranking itself doesn't shrink to fit whatever
    filters happen to be applied, only which page of it is shown does.

    Default sort_by="recent" behaves exactly as before: ordered by
    (scraped_at, id) rather than scraped_at alone, since many rows share an
    identical scraped_at (batch inserts) and scraped_at-only ordering is
    not guaranteed stable across separate queries when there's a tie —
    verified against the real DB, where that made different pages return
    overlapping rows. id is unique, so the tiebreaker makes paging
    deterministic and gapless.

    price_negotiable listings additionally (never simultaneously — see
    deal_percentages()) carry estimated_price/estimated_price_per_sqm/
    estimate_basis from analytics.estimate_negotiable_price(), an
    unconfirmed estimate derived from the same comparable group's real
    prices — None when that function has no comparable group for them
    either. A negotiable listing's own `price` field stays whatever
    placeholder the source shows (e.g. "170 ₮ Үнэ тохирно" parses to a
    token value like 169); callers must not treat it as real, and should
    prefer estimated_price with clear "estimated, unconfirmed" labeling.

    Every listing also carries group_median_price_per_sqm (the same group
    baseline deal_pct was computed against, as an absolute number — for a
    detail view showing "your price/m² vs the group's") and
    rental_yield_pct/_payback_years/_n_sale/_n_rent, matched by
    (district, rooms) against analytics.rental_yield_by_district_rooms()
    (Week 5, unchanged) regardless of this listing's own listing_type,
    since that bucket already reflects a sale/rent pairing. Both are None
    when there's no matching bucket (non-apartments, or no comparable
    rent-side data for that district+room-count) — callers should say so
    plainly rather than guessing a number.
    """
    excluded_ids = superseded_listing_ids_conn(settings.database_url)
    deals_by_id = {d["id"]: d for d in deal_percentages_conn(settings.database_url)}
    complex_deals_by_id = {d["id"]: d for d in complex_deal_percentages_conn(settings.database_url)}
    estimates_by_id = {e["id"]: e for e in estimate_negotiable_price_conn(settings.database_url)}
    yield_by_district_rooms = {
        (y["district"], y["rooms"]): y for y in rental_yield_by_district_rooms_conn(settings.database_url)
    }

    if sort_by == "deal_pct":
        # deal_percentages() already excludes superseded listings itself, so
        # every id in deals_by_id is already canonical -- no need to filter
        # excluded_ids again here.
        #
        # Restricted to deal_status == "top_deal": deal_pct itself is sorted
        # best-first regardless of status, so without this a "surface the
        # most underpriced listings" sort would put 'needs_review' rows
        # (test ads, "170 ₮ Үнэ тохирно" placeholders, area-parsing bugs --
        # exactly the noise the confidence tiers exist to keep out of a
        # confident deals list) at the very top, ahead of every genuine deal.
        candidate_ids = [
            deal_id
            for deal_id, deal in deals_by_id.items()
            if deal["deal_status"] == "top_deal"
            and (district is None or deal["district"] == district)
            and (property_type is None or deal["property_type"] == property_type)
            and (min_price is None or float(deal["price"]) >= min_price)
            and (max_price is None or float(deal["price"]) <= max_price)
        ]
        page_ids = candidate_ids[offset:offset + limit]
        if not page_ids:
            return []
        rows_by_id = {row.id: row for row in db.query(Listing).filter(Listing.id.in_(page_ids)).all()}
        ordered = [rows_by_id[i] for i in page_ids if i in rows_by_id]
    else:
        query = db.query(Listing).filter(Listing.id.notin_(excluded_ids))
        if district is not None:
            query = query.filter(Listing.district == district)
        if property_type is not None:
            query = query.filter(Listing.property_type == property_type)
        if min_price is not None:
            query = query.filter(Listing.price >= min_price)
        if max_price is not None:
            query = query.filter(Listing.price <= max_price)
        ordered = (
            query.order_by(Listing.scraped_at.desc(), Listing.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    return [
        _attach_computed_fields(
            listing,
            deals_by_id.get(listing.id),
            complex_deals_by_id.get(listing.id),
            estimates_by_id.get(listing.id),
            yield_by_district_rooms.get((listing.district, listing.rooms)),
        )
        for listing in ordered
    ]
