-- PostgreSQL schema for the real estate analytics platform.
-- Requires PostgreSQL 12+ (generated columns).
-- Tables will be added as V1.0 features are implemented.

CREATE TABLE IF NOT EXISTS listings (
    id              BIGSERIAL PRIMARY KEY,

    source          VARCHAR(20) NOT NULL CHECK (source IN ('unegui', 'facebook')),
    source_url      TEXT NOT NULL,

    title           TEXT NOT NULL,
    description     TEXT,

    price           NUMERIC(14, 2),
    area_sqm        NUMERIC(10, 2),
    -- Derived from price/area_sqm so it stays consistent with the source values;
    -- NULL when either input is missing or area_sqm is not positive.
    price_per_sqm   NUMERIC(14, 2) GENERATED ALWAYS AS (
                        CASE WHEN area_sqm > 0 THEN ROUND(price / area_sqm, 2) ELSE NULL END
                    ) STORED,

    rooms           SMALLINT,
    district        TEXT,
    address         TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,

    contact_phone   TEXT,
    photo_urls      TEXT[] NOT NULL DEFAULT '{}',

    -- Hash of normalized listing attributes, used to find cross-source duplicate
    -- candidates (e.g. the same unit posted on both Unegui and Facebook).
    -- Intentionally not unique: duplicates are resolved by app logic, not the DB.
    dedup_hash      TEXT NOT NULL,

    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Same source_url re-scraped should upsert the existing row, not duplicate it.
    CONSTRAINT uq_listings_source_url UNIQUE (source, source_url)
);

CREATE INDEX IF NOT EXISTS idx_listings_dedup_hash ON listings (dedup_hash);

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
