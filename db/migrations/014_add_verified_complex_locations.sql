-- 014: independently reviewed location allowlist for complex assignments.
-- Unregistered complexes retain the existing conservative alias behaviour;
-- registered complexes may only be attached inside an explicitly verified
-- district.  Khoroo is retained as evidence but is not yet an assignment
-- gate because source address coverage is incomplete.

CREATE TABLE IF NOT EXISTS verified_complex_locations (
    id               BIGSERIAL PRIMARY KEY,
    complex_id       BIGINT NOT NULL REFERENCES complexes(id) ON DELETE CASCADE,
    district         TEXT NOT NULL,
    khoroo            SMALLINT,
    evidence_text     TEXT NOT NULL,
    registry_version  TEXT NOT NULL,
    verified_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (complex_id, district, registry_version)
);

CREATE INDEX IF NOT EXISTS idx_verified_complex_locations_complex
    ON verified_complex_locations (complex_id);

-- Session 0 Batch 2 titles were individually reviewed: the old name was a
-- landmark and the target below was the actual unit, consistently in Хан-Уул.
INSERT INTO verified_complex_locations
    (complex_id, district, evidence_text, registry_version)
SELECT c.id, 'Хан-Уул', 'Session 0 Batch 2 human-reviewed unit evidence', 'session0-v1'
FROM complexes c
WHERE c.canonical_name = ANY (ARRAY[
    'Жаргалан', 'Нархан', 'SS Garden', 'Агниста', 'Рапид',
    'Sky Garden Residence', 'River Tower', 'Modun Town', 'River Plaza',
    'Академи 1', 'Khan Hills'
])
ON CONFLICT (complex_id, district, registry_version) DO NOTHING;
