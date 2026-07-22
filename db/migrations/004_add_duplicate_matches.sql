-- 004: duplicate_matches — scored duplicate-candidate pairs between listings.
--
-- A separate table (rather than a duplicate_of column on listings) keeps
-- match decisions auditable and re-scorable: rows carry the score and the
-- time of scoring, and re-running the scorer upserts in place. Pairs are
-- stored once with listing_id_a < listing_id_b enforced.

CREATE TABLE IF NOT EXISTS duplicate_matches (
    listing_id_a  BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    listing_id_b  BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    score         DOUBLE PRECISION NOT NULL,
    matched_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (listing_id_a, listing_id_b),
    CONSTRAINT ck_duplicate_matches_order CHECK (listing_id_a < listing_id_b)
);

-- The PK covers lookups by listing_id_a; this covers the other side.
CREATE INDEX IF NOT EXISTS idx_duplicate_matches_b ON duplicate_matches (listing_id_b);
