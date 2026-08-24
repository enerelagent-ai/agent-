from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import and_, func

from analytics.matches import superseded_listing_ids_conn
from app.api.deps import DbSession
from app.config import settings
from app.models.listing import Complex, Listing, ListingComplexMatch
from app.schemas.complex import ComplexIntelligenceDetail, ComplexIntelligenceSummary

router = APIRouter(prefix="/complexes", tags=["complexes"])


def _summary_query(db: DbSession):
    excluded_ids = superseded_listing_ids_conn(settings.database_url)
    approved = and_(
        ListingComplexMatch.listing_id == Listing.id,
        ListingComplexMatch.complex_id == Listing.complex_id,
        ListingComplexMatch.is_current.is_(True),
        ListingComplexMatch.relation == "unit",
        ListingComplexMatch.review_status == "approved",
    )
    sale = Listing.listing_type == "sale"
    rent = Listing.listing_type == "rent"
    valid_ppsqm = and_(sale, Listing.price_per_sqm.is_not(None), Listing.price_per_sqm > 0)

    return (
        db.query(
            Complex.id.label("id"),
            Complex.canonical_name.label("name"),
            func.mode().within_group(Listing.district).label("district"),
            func.count(func.distinct(Listing.id)).label("active_listings"),
            func.count(func.distinct(Listing.id)).filter(sale).label("sale_listings"),
            func.count(func.distinct(Listing.id)).filter(rent).label("rent_listings"),
            func.percentile_cont(0.5).within_group(Listing.price_per_sqm).filter(valid_ppsqm).label("median_sale_price_per_sqm"),
            func.min(Listing.price_per_sqm).filter(valid_ppsqm).label("min_sale_price_per_sqm"),
            func.max(Listing.price_per_sqm).filter(valid_ppsqm).label("max_sale_price_per_sqm"),
            func.avg(Listing.lat).filter(and_(Listing.lat.is_not(None), Listing.lng.is_not(None))).label("lat"),
            func.avg(Listing.lng).filter(and_(Listing.lat.is_not(None), Listing.lng.is_not(None))).label("lng"),
            func.max(Listing.scraped_at).label("data_as_of"),
        )
        .join(Listing, Listing.complex_id == Complex.id)
        .join(ListingComplexMatch, approved)
        .filter(
            Listing.is_active.is_(True),
            Listing.id.notin_(excluded_ids),
        )
        .group_by(Complex.id, Complex.canonical_name)
    )


def _serialize(row) -> dict:
    data = dict(row._mapping)
    data["lat"] = float(data["lat"]) if data["lat"] is not None else None
    data["lng"] = float(data["lng"]) if data["lng"] is not None else None
    for key in ("median_sale_price_per_sqm", "min_sale_price_per_sqm", "max_sale_price_per_sqm"):
        data[key] = float(data[key]) if data[key] is not None else None
    data["location_kind"] = "listing_centroid" if data["lat"] is not None else "unknown"
    data["has_contour"] = False
    return data


@router.get("", response_model=list[ComplexIntelligenceSummary])
def list_complex_intelligence(
    db: DbSession,
    district: str | None = Query(None),
    q: str | None = Query(None, min_length=1, max_length=100),
) -> list[dict]:
    query = _summary_query(db)
    if q:
        query = query.filter(Complex.canonical_name.ilike(f"%{q.strip()}%"))
    rows = query.order_by(func.count(func.distinct(Listing.id)).desc(), Complex.canonical_name).all()
    serialized = [_serialize(row) for row in rows]
    if district:
        serialized = [row for row in serialized if row["district"] == district]
    return serialized


@router.get("/{complex_id}", response_model=ComplexIntelligenceDetail)
def get_complex_intelligence(complex_id: int, db: DbSession) -> dict:
    row = _summary_query(db).filter(Complex.id == complex_id).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Verified complex not found")
    complex_row = db.query(Complex).filter(Complex.id == complex_id).one()
    result = _serialize(row)
    result["aliases"] = complex_row.aliases or []

    approved_listing_ids = (
        db.query(ListingComplexMatch.listing_id)
        .filter(
            ListingComplexMatch.complex_id == complex_id,
            ListingComplexMatch.is_current.is_(True),
            ListingComplexMatch.relation == "unit",
            ListingComplexMatch.review_status == "approved",
        )
    )
    sale_prices = db.query(Listing.price).filter(
        Listing.id.in_(approved_listing_ids), Listing.is_active.is_(True),
        Listing.listing_type == "sale", Listing.price.is_not(None), Listing.price > 0,
    )
    rent_prices = db.query(Listing.price).filter(
        Listing.id.in_(approved_listing_ids), Listing.is_active.is_(True),
        Listing.listing_type == "rent", Listing.price.is_not(None), Listing.price > 0,
    )
    result["median_sale_price"] = sale_prices.with_entities(
        func.percentile_cont(0.5).within_group(Listing.price)
    ).scalar()
    result["median_rent_price"] = rent_prices.with_entities(
        func.percentile_cont(0.5).within_group(Listing.price)
    ).scalar()
    return result

