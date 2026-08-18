-- 013: complex_link_audit — audit trail for every automated complex_id
-- correction (Session 0/0.5, landmark-cue fix follow-up).
--
-- A listing's complex_id is never just NULL-ed or overwritten silently:
-- each unlink or reassignment is recorded here first, so a future reader
-- can answer "why did this listing's complex change" without re-deriving
-- it from the extractor's current (possibly further-evolved) behaviour.
-- Mirrors listings.is_active's soft-delete philosophy (migration 009) —
-- history stays queryable, nothing is thrown away.

CREATE TABLE IF NOT EXISTS complex_link_audit (
    id              BIGSERIAL PRIMARY KEY,

    listing_id      BIGINT NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    action          TEXT NOT NULL CHECK (action IN ('unlink', 'reassign')),

    -- old_complex_id is NOT a FK: the whole point is to keep the audit row
    -- readable even if the complex itself is later merged/deleted. The
    -- canonical name is captured as text for the same reason.
    old_complex_id      BIGINT,
    old_complex_name    TEXT NOT NULL,
    new_complex_id       BIGINT REFERENCES complexes(id) ON DELETE SET NULL,
    new_complex_name     TEXT,

    reason          TEXT NOT NULL,
    evidence_text   TEXT,
    district        TEXT,

    -- Which apply script run produced this row -- lets a future run tell
    -- its own corrections apart from an earlier pass's.
    script_version  TEXT NOT NULL,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_complex_link_audit_listing ON complex_link_audit (listing_id);
