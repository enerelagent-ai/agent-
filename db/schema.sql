-- PostgreSQL schema for the real estate analytics platform.
-- Requires PostgreSQL 12+ (generated columns).
-- Tables will be added as V1.0 features are implemented.

CREATE TABLE IF NOT EXISTS listings (
    id              BIGSERIAL PRIMARY KEY,

    source          VARCHAR(20) NOT NULL CHECK (source IN ('unegui', 'facebook')),
    source_url      TEXT NOT NULL,

    title           TEXT NOT NULL,
    description     TEXT,

    price           NUMERIC(18, 2),
    -- Display price text as shown on the ad (keeps discount info:
    -- "7.9 сая ₮ 8.9 сая ₮ Үнэ тохирно").
    price_raw       TEXT,
    -- "Үнэ тохирно" on the ad; NULL = unknown (no price text seen yet).
    price_negotiable BOOLEAN,
    area_sqm        NUMERIC(10, 2),
    -- Derived from price/area_sqm so it stays consistent with the source values;
    -- NULL when either input is missing or area_sqm is not positive.
    price_per_sqm   NUMERIC(18, 2) GENERATED ALWAYS AS (
                        CASE WHEN area_sqm > 0 THEN ROUND(price / area_sqm, 2) ELSE NULL END
                    ) STORED,

    -- Sale and rent prices differ by ~100x, so every price statistic must be
    -- computed within one transaction type. Nullable: V2 sources (Facebook)
    -- may not always make the type determinable.
    listing_type    TEXT CHECK (listing_type IN ('sale', 'rent')),

    -- Raw Unegui breadcrumb category (e.g. 'Орон сууц зарна'); price-per-sqm
    -- comparisons are only meaningful within one property type. Subtype is
    -- optional; for apartments it carries the room count (e.g. '3 өрөө').
    property_type   TEXT,
    property_subtype TEXT,

    rooms           SMALLINT,
    -- Normalized from generic specs ("Хэдэн давхарт" / "Барилгын давхар").
    floor           SMALLINT,
    total_floors    SMALLINT,
    district        TEXT,
    address         TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,

    contact_phone   TEXT,
    photo_urls      TEXT[] NOT NULL DEFAULT '{}',
    -- Latest cumulative detail-page counter reported by the source.
    view_count      INTEGER CHECK (view_count IS NULL OR view_count >= 0),

    -- Hash of normalized listing attributes, used to find cross-source duplicate
    -- candidates (e.g. the same unit posted on both Unegui and Facebook).
    -- Intentionally not unique: duplicates are resolved by app logic, not the DB.
    dedup_hash      TEXT NOT NULL,

    -- When the ad was published on the source site (source-local time);
    -- NULL when the source's relative date could not be resolved.
    posted_at       TIMESTAMPTZ,
    -- Original posted-date text ("Өнөөдөр 19:05", "2026-07-05 19:06") as
    -- parse evidence / backfill source.
    posted_raw      TEXT,

    -- Full key-value spec list from the ad (Шал, Тагт, Ашиглалтанд орсон
    -- он, ...); keys vary by listing type, so kept as raw JSONB for later
    -- extraction without re-scraping.
    specs           JSONB NOT NULL DEFAULT '{}'::jsonb,

    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Same source_url re-scraped should upsert the existing row, not duplicate it.
    CONSTRAINT uq_listings_source_url UNIQUE (source, source_url)
);

CREATE TABLE IF NOT EXISTS complexes (
    id              BIGSERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,
    normalized_name TEXT NOT NULL UNIQUE,
    aliases         TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE listings ADD COLUMN IF NOT EXISTS complex_id BIGINT
    REFERENCES complexes(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_listings_dedup_hash ON listings (dedup_hash);
CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings (property_type);
CREATE INDEX IF NOT EXISTS idx_listings_complex_id ON listings (complex_id);
CREATE INDEX IF NOT EXISTS idx_listings_floor ON listings (floor);

-- Scored duplicate-candidate pairs (see migration 004): kept separate from
-- listings so match decisions stay auditable and re-scorable. One row per
-- pair, listing_id_a < listing_id_b.
CREATE TABLE IF NOT EXISTS duplicate_matches (
    listing_id_a  BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    listing_id_b  BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    score         DOUBLE PRECISION NOT NULL,
    matched_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (listing_id_a, listing_id_b),
    CONSTRAINT ck_duplicate_matches_order CHECK (listing_id_a < listing_id_b)
);

CREATE INDEX IF NOT EXISTS idx_duplicate_matches_b ON duplicate_matches (listing_id_b);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_listings_updated_at ON listings;
CREATE TRIGGER trg_listings_updated_at
    BEFORE UPDATE ON listings
    FOR EACH ROW
    EXECUTE FUNCTION set_updated_at();
