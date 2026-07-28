-- 008: price_history — one snapshot row per (date, listing_type,
-- property_type, district) each time the market calculation is run.
--
-- listing_type/property_type are part of the grain (not just district) so a
-- snapshot never blends sale with rent, or apartments with land — the same
-- ~100x sale-vs-rent price gap that shaped listings.listing_type (see
-- db/schema.sql) applies here. A snapshot is produced by re-running
-- average_price_by_group() and inserting its rows with today's date, so the
-- table naturally grows one generation richer every time it runs (manual
-- today, Week 7's scheduled job later) with no code changes required.

CREATE TABLE IF NOT EXISTS price_history (
    id                BIGSERIAL PRIMARY KEY,

    snapshot_date     DATE NOT NULL,
    listing_type      TEXT NOT NULL,
    property_type     TEXT NOT NULL,
    district          TEXT NOT NULL,

    n_listings        INTEGER NOT NULL,
    avg_price         NUMERIC(18, 2),
    avg_price_per_sqm NUMERIC(18, 2),

    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Re-running the snapshot on the same day upserts in place rather than
    -- accumulating duplicate rows for that day.
    CONSTRAINT uq_price_history_snapshot
        UNIQUE (snapshot_date, listing_type, property_type, district)
);

CREATE INDEX IF NOT EXISTS idx_price_history_slice
    ON price_history (listing_type, property_type, district, snapshot_date);
