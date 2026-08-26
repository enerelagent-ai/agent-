-- Licensed public affordability snapshot imported from hotkhon.mn/bolomj/.
-- The payload contains only area, asking price and district; no seller or
-- contact information is copied. Keeping snapshots makes provenance explicit.

CREATE TABLE IF NOT EXISTS public_affordability_snapshots (
    source          TEXT NOT NULL,
    data_as_of      DATE NOT NULL,
    source_url      TEXT NOT NULL,
    districts       JSONB NOT NULL,
    listings        JSONB NOT NULL,
    rules           JSONB NOT NULL,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (source, data_as_of)
);

