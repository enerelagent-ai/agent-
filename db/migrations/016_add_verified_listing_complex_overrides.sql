-- 016: exact listing-level exceptions for verified complex assignments when
-- the source location dropdown conflicts with stronger independent evidence.
-- This is intentionally keyed by source URL and complex; it never weakens a
-- district guard for other listings.

CREATE TABLE IF NOT EXISTS verified_listing_complex_overrides (
    id                BIGSERIAL PRIMARY KEY,
    source            TEXT NOT NULL,
    source_url        TEXT NOT NULL,
    complex_id        BIGINT NOT NULL REFERENCES complexes(id) ON DELETE CASCADE,
    reason            TEXT NOT NULL,
    evidence_text     TEXT NOT NULL,
    registry_version  TEXT NOT NULL,
    verified_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, source_url, complex_id)
);

CREATE INDEX IF NOT EXISTS idx_verified_listing_complex_override_lookup
    ON verified_listing_complex_overrides (source, source_url, complex_id);

INSERT INTO verified_listing_complex_overrides
    (source, source_url, complex_id, reason, evidence_text, registry_version)
SELECT l.source, l.source_url, c.id,
       'source district conflicts with independently verified River Plaza location',
       'Exact listing names River Plaza; coordinates and multiple independent River Plaza listings place the complex in Хан-Уул 17',
       'session0-v1'
FROM listings l
JOIN complexes c ON c.canonical_name = 'River Plaza'
WHERE l.id = 26438
  AND l.source_url = 'https://www.unegui.mn/adv/9556094_uilchilgeenii-talboi-khudaldana/'
ON CONFLICT (source, source_url, complex_id) DO NOTHING;
