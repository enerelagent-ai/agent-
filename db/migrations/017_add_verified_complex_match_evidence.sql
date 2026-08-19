-- 017: normalize complex aliases and persist extraction evidence separately
-- from the convenience pointer on listings.complex_id.
--
-- listings.complex_id remains in place for existing marketplace/analytics
-- reads. listing_complex_matches is the reviewable source of truth introduced
-- by Release 3; a later migration can derive the pointer from approved rows
-- once the pilot data has been reviewed.

CREATE TABLE IF NOT EXISTS complex_aliases (
    id                BIGSERIAL PRIMARY KEY,
    complex_id        BIGINT NOT NULL REFERENCES complexes(id) ON DELETE CASCADE,
    alias             TEXT NOT NULL,
    normalized_alias  TEXT NOT NULL,
    source            TEXT NOT NULL DEFAULT 'reviewed'
        CHECK (source IN ('canonical', 'reviewed', 'discovered')),
    is_active         BOOLEAN NOT NULL DEFAULT true,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (normalized_alias)
);

CREATE INDEX IF NOT EXISTS idx_complex_aliases_complex
    ON complex_aliases (complex_id);

-- Seed canonical names and the reviewed alias arrays already maintained by
-- migration 010/backfill_complexes.py. ON CONFLICT intentionally refuses to
-- let the same normalized alias silently identify two different complexes.
INSERT INTO complex_aliases (complex_id, alias, normalized_alias, source)
SELECT id, canonical_name, normalized_name, 'canonical'
FROM complexes
ON CONFLICT (normalized_alias) DO NOTHING;

INSERT INTO complex_aliases (complex_id, alias, normalized_alias, source)
SELECT c.id,
       a.alias,
       trim(regexp_replace(lower(a.alias), '[^[:alnum:]]+', ' ', 'g')),
       'reviewed'
FROM complexes c
CROSS JOIN LATERAL unnest(c.aliases) AS a(alias)
WHERE trim(a.alias) <> ''
ON CONFLICT (normalized_alias) DO NOTHING;

CREATE TABLE IF NOT EXISTS listing_complex_matches (
    id                 BIGSERIAL PRIMARY KEY,
    listing_id         BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    complex_id         BIGINT NOT NULL REFERENCES complexes(id) ON DELETE CASCADE,
    matched_alias_id   BIGINT REFERENCES complex_aliases(id) ON DELETE SET NULL,
    relation           TEXT NOT NULL
        CHECK (relation IN ('unit', 'landmark', 'unknown')),
    confidence         NUMERIC(4, 3) NOT NULL
        CHECK (confidence >= 0 AND confidence <= 1),
    evidence_text      TEXT NOT NULL,
    source_field       TEXT NOT NULL DEFAULT 'title'
        CHECK (source_field IN ('title', 'description', 'address', 'manual')),
    extractor_version  TEXT NOT NULL,
    review_status      TEXT NOT NULL DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'approved', 'rejected')),
    reviewer_note      TEXT,
    reviewed_at        TIMESTAMPTZ,
    is_current         BOOLEAN NOT NULL DEFAULT true,
    detected_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT listing_complex_match_review_consistency CHECK (
        (review_status = 'pending' AND reviewed_at IS NULL)
        OR (review_status IN ('approved', 'rejected') AND reviewed_at IS NOT NULL)
    ),
    UNIQUE (listing_id, complex_id, extractor_version, evidence_text)
);

CREATE INDEX IF NOT EXISTS idx_listing_complex_matches_listing_current
    ON listing_complex_matches (listing_id, is_current);
CREATE INDEX IF NOT EXISTS idx_listing_complex_matches_review_queue
    ON listing_complex_matches (review_status, detected_at)
    WHERE is_current;
CREATE INDEX IF NOT EXISTS idx_listing_complex_matches_complex
    ON listing_complex_matches (complex_id, relation, review_status);

