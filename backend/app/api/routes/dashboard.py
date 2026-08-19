from datetime import datetime, timezone
from typing import Literal

from analytics.calculations import (
    complex_average_price_conn,
    complex_deal_percentages_conn,
    deal_percentages_conn,
    estimate_negotiable_price_conn,
    investment_summary_by_district_conn,
    listing_counts_by_property_type_conn,
    monthly_delisting_trend_conn,
    price_trend_conn,
    rental_yield_by_district_rooms_conn,
    todays_opportunity_conn,
)
from analytics.matches import superseded_listing_ids_conn
from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.api.routes.listings import attach_complex_metadata
from app.config import settings
from app.models.listing import Complex, ComplexAlias, Listing, ListingComplexMatch, NotificationState
from app.schemas.dashboard import (
    DistrictInvestmentSummary,
    DealAlertFeed,
    ComplexPriceSummary,
    ComplexOption,
    ComplexReviewQueue,
    ListingTypeCount,
    MonthlyDelistingPoint,
    NotificationReadState,
    PriceTrendPoint,
    TodaysOpportunity,
)
from app.schemas.listing import ListingOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _deal_candidate_ids(
    deals_by_id: dict[int, dict],
    status: str,
    listing_type: str | None,
    district: str | None,
    property_type: str | None,
    complex_id: int | None,
    min_price: float | None,
    max_price: float | None,
) -> list[int]:
    """Preserve analytics deal ranking while applying browse filters."""
    return [
        deal_id
        for deal_id, deal in deals_by_id.items()
        if deal["deal_status"] == status
        and (listing_type is None or deal["listing_type"] == listing_type)
        and (district is None or deal["district"] == district)
        and (property_type is None or deal["property_type"] == property_type)
        and (complex_id is None or deal["complex_id"] == complex_id)
        and (min_price is None or float(deal["price"]) >= min_price)
        and (max_price is None or float(deal["price"]) <= max_price)
    ]


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
    analytics.calculations.price_trend for why. It has one point per day that
    the scheduled scraper pipeline has completed a market-price snapshot.
    """
    return price_trend_conn(settings.database_url, listing_type, property_type)


@router.get("/listing-counts-by-type", response_model=list[ListingTypeCount])
def listing_counts_by_type() -> list[dict]:
    return listing_counts_by_property_type_conn(settings.database_url)


@router.get("/delisting-trend", response_model=list[MonthlyDelistingPoint])
def delisting_trend(
    listing_type: Literal["sale", "rent"] | None = Query(None),
    district: str | None = Query(None),
) -> list[dict]:
    """Monthly removed-ad counts; removal does not necessarily mean a sale."""
    return monthly_delisting_trend_conn(settings.database_url, listing_type, district)


def _notification_state(db: DbSession) -> NotificationState:
    state = db.get(NotificationState, 1)
    if state is None:
        now = datetime.now(timezone.utc)
        state = NotificationState(id=1, last_seen_at=now, updated_at=now)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/deal-alerts", response_model=DealAlertFeed)
def deal_alerts(db: DbSession, limit: int = Query(20, ge=1, le=100)) -> dict:
    """Current confident deals plus a single-admin unread count."""
    state = _notification_state(db)
    deals = {
        row["id"]: row
        for row in deal_percentages_conn(settings.database_url)
        if row["deal_status"] == "top_deal"
    }
    if not deals:
        return {"items": [], "unseen_count": 0, "last_seen_at": state.last_seen_at}

    rows = (
        db.query(Listing)
        .filter(Listing.id.in_(deals), Listing.is_active.is_(True))
        .order_by(Listing.scraped_at.desc(), Listing.id.desc())
        .all()
    )
    unseen_count = sum(1 for row in rows if row.scraped_at > state.last_seen_at)
    page = rows[:limit]
    complex_ids = {row.complex_id for row in page if row.complex_id is not None}
    complex_names = {
        row.id: row.canonical_name
        for row in db.query(Complex).filter(Complex.id.in_(complex_ids)).all()
    } if complex_ids else {}
    return {
        "items": [
            {
                "id": row.id,
                "title": row.title,
                "source_url": row.source_url,
                "price": float(row.price) if row.price is not None else None,
                "district": row.district,
                "complex_name": complex_names.get(row.complex_id),
                "scraped_at": row.scraped_at,
                "deal_pct": float(deals[row.id]["deal_pct"]),
            }
            for row in page
        ],
        "unseen_count": unseen_count,
        "last_seen_at": state.last_seen_at,
    }


@router.post("/deal-alerts/mark-seen", response_model=NotificationReadState)
def mark_deal_alerts_seen(db: DbSession) -> dict:
    state = _notification_state(db)
    now = datetime.now(timezone.utc)
    state.last_seen_at = now
    state.updated_at = now
    db.commit()
    return {"last_seen_at": now}


@router.get("/complex-prices", response_model=list[ComplexPriceSummary])
def complex_prices(complex_id: int | None = Query(None, ge=1)) -> list[dict]:
    """Current canonical price statistics, optionally for one complex."""
    return complex_average_price_conn(settings.database_url, complex_id)


@router.get("/complexes", response_model=list[ComplexOption])
def complexes(db: DbSession) -> list[dict]:
    """Canonical complexes that currently have at least one active listing."""
    rows = (
        db.query(Complex.id, Complex.canonical_name)
        .join(Listing, Listing.complex_id == Complex.id)
        .filter(Listing.is_active.is_(True))
        .distinct()
        .order_by(Complex.canonical_name)
        .all()
    )
    return [{"id": row.id, "canonical_name": row.canonical_name} for row in rows]


@router.get("/complex-review-queue", response_model=ComplexReviewQueue)
def complex_review_queue(
    db: DbSession,
    relation: Literal["unit", "landmark", "unknown"] | None = Query(None),
    complex_id: int | None = Query(None, ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """Current pending complex evidence; read-only human-review workspace."""
    base = (
        db.query(ListingComplexMatch)
        .filter(
            ListingComplexMatch.is_current.is_(True),
            ListingComplexMatch.review_status == "pending",
        )
    )
    pending_unit = base.filter(ListingComplexMatch.relation == "unit").count()
    pending_landmark = base.filter(ListingComplexMatch.relation == "landmark").count()
    filtered = base
    if relation is not None:
        filtered = filtered.filter(ListingComplexMatch.relation == relation)
    if complex_id is not None:
        filtered = filtered.filter(ListingComplexMatch.complex_id == complex_id)
    total = filtered.count()
    matches = (
        filtered.order_by(
            ListingComplexMatch.confidence.desc(),
            ListingComplexMatch.detected_at.desc(),
            ListingComplexMatch.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    listing_ids = [row.listing_id for row in matches]
    complex_ids = {row.complex_id for row in matches}
    alias_ids = {row.matched_alias_id for row in matches if row.matched_alias_id is not None}
    listings = {
        row.id: row for row in db.query(Listing).filter(Listing.id.in_(listing_ids)).all()
    } if listing_ids else {}
    complexes_by_id = {
        row.id: row.canonical_name
        for row in db.query(Complex).filter(Complex.id.in_(complex_ids)).all()
    } if complex_ids else {}
    aliases = {
        row.id: row.alias
        for row in db.query(ComplexAlias).filter(ComplexAlias.id.in_(alias_ids)).all()
    } if alias_ids else {}
    items = []
    for match in matches:
        listing = listings[match.listing_id]
        note = match.reviewer_note or ""
        reason = note.split(": ", 1)[1] if note.startswith("legacy pending-match backfill") else note or None
        items.append({
            "listing_id": listing.id,
            "complex_id": match.complex_id,
            "complex_name": complexes_by_id[match.complex_id],
            "matched_alias": aliases.get(match.matched_alias_id),
            "relation": match.relation,
            "confidence": float(match.confidence),
            "evidence_text": match.evidence_text,
            "district": listing.district,
            "address": listing.address,
            "source_url": listing.source_url,
            "review_reason": reason,
            "detected_at": match.detected_at,
        })
    return {
        "items": items,
        "total": total,
        "pending_unit": pending_unit,
        "pending_landmark": pending_landmark,
        "limit": limit,
        "offset": offset,
    }


def _attach_computed_fields(
    listing: Listing,
    deal: dict | None,
    complex_deal: dict | None,
    complex_name: str | None,
    estimate: dict | None,
    yield_info: dict | None,
) -> Listing:
    listing.deal_pct = float(deal["deal_pct"]) if deal else None
    listing.deal_status = deal["deal_status"] if deal else None
    listing.deal_reason = deal["deal_reason"] if deal else None
    listing.n_comparable = deal["n_comparable"] if deal else None
    listing.group_median_price_per_sqm = float(deal["group_median_price_per_sqm"]) if deal else None
    listing.complex_name = complex_name
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
    listing_type: Literal["sale", "rent"] | None = Query(None),
    district: str | None = Query(None),
    property_type: str | None = Query(None),
    complex_id: int | None = Query(None, ge=1),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    deal_status: Literal["top_deal", "needs_review", "not_notable"] | None = Query(None),
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

    deal_status optionally restricts the browse result to one of those
    explicit confidence classes. In particular, needs_review remains a
    manual data-quality queue and is never folded into the default
    sort_by="deal_pct" top-deal list.

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

    status_candidate_ids = (
        _deal_candidate_ids(
            deals_by_id,
            deal_status,
            listing_type,
            district,
            property_type,
            complex_id,
            min_price,
            max_price,
        )
        if deal_status is not None
        else None
    )

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
        candidate_ids = (
            status_candidate_ids
            if status_candidate_ids is not None
            else _deal_candidate_ids(
                deals_by_id,
                "top_deal",
                listing_type,
                district,
                property_type,
                complex_id,
                min_price,
                max_price,
            )
        )
        page_ids = candidate_ids[offset:offset + limit]
        if not page_ids:
            return []
        rows_by_id = {row.id: row for row in db.query(Listing).filter(Listing.id.in_(page_ids)).all()}
        ordered = [rows_by_id[i] for i in page_ids if i in rows_by_id]
    else:
        query = db.query(Listing).filter(
            Listing.id.notin_(excluded_ids),
            Listing.is_active.is_(True),
        )
        if status_candidate_ids is not None:
            if not status_candidate_ids:
                return []
            query = query.filter(Listing.id.in_(status_candidate_ids))
        if district is not None:
            query = query.filter(Listing.district == district)
        if listing_type is not None:
            query = query.filter(Listing.listing_type == listing_type)
        if property_type is not None:
            query = query.filter(Listing.property_type == property_type)
        if complex_id is not None:
            query = query.filter(Listing.complex_id == complex_id)
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

    attach_complex_metadata(db, ordered)

    return [
        _attach_computed_fields(
            listing,
            deals_by_id.get(listing.id),
            complex_deals_by_id.get(listing.id),
            listing.complex_name,
            estimates_by_id.get(listing.id),
            yield_by_district_rooms.get((listing.district, listing.rooms)),
        )
        for listing in ordered
    ]
