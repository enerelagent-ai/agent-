-- Licensed public republication feed imported from hotkhon.mn public pages.
-- Kept separate from our independently verified registry: source provenance,
-- cutoff date and raw derived fields remain auditable and reversible.

CREATE TABLE IF NOT EXISTS public_complex_profiles (
    source              TEXT NOT NULL,
    source_slug         TEXT NOT NULL,
    source_url          TEXT NOT NULL,
    canonical_name      TEXT NOT NULL,
    district            TEXT,
    median_price_per_sqm NUMERIC(14, 2),
    active_listings     INTEGER NOT NULL DEFAULT 0,
    lat                 DOUBLE PRECISION,
    lng                 DOUBLE PRECISION,
    photo_url           TEXT,
    has_contour         BOOLEAN NOT NULL DEFAULT false,
    location_kind       TEXT,
    data_as_of          DATE NOT NULL,
    profile_metrics     JSONB NOT NULL DEFAULT '{}'::jsonb,
    scraped_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, source_slug)
);

CREATE INDEX IF NOT EXISTS idx_public_complex_profiles_district
    ON public_complex_profiles (district);
CREATE INDEX IF NOT EXISTS idx_public_complex_profiles_name
    ON public_complex_profiles (lower(canonical_name));

CREATE TABLE IF NOT EXISTS public_complex_contours (
    id                  BIGSERIAL PRIMARY KEY,
    source              TEXT NOT NULL,
    source_slug         TEXT NOT NULL,
    polygon_index       INTEGER NOT NULL,
    location_kind       TEXT,
    geometry            JSONB NOT NULL,
    data_as_of          DATE NOT NULL,
    scraped_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_slug, polygon_index),
    FOREIGN KEY (source, source_slug)
        REFERENCES public_complex_profiles(source, source_slug) ON DELETE CASCADE
);

