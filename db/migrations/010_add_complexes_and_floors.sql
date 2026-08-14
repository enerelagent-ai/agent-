-- 010: normalized residential/commercial complex identity and real floor columns.
-- Raw specs remain intact; these columns make filtering/indexing possible.

CREATE TABLE IF NOT EXISTS complexes (
    id              BIGSERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL UNIQUE,
    normalized_name TEXT NOT NULL UNIQUE,
    aliases         TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE listings ADD COLUMN IF NOT EXISTS floor SMALLINT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS total_floors SMALLINT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS complex_id BIGINT
    REFERENCES complexes(id) ON DELETE SET NULL;

-- Both Unegui fields are numeric in the refreshed DB except "25+" for the
-- building total; the leading integer is the useful normalized value.
UPDATE listings
SET floor = substring(specs->>'Хэдэн давхарт' FROM '^([0-9]+)')::SMALLINT
WHERE floor IS NULL AND specs ? 'Хэдэн давхарт'
  AND specs->>'Хэдэн давхарт' ~ '^[0-9]+';

UPDATE listings
SET total_floors = substring(specs->>'Барилгын давхар' FROM '^([0-9]+)')::SMALLINT
WHERE total_floors IS NULL AND specs ? 'Барилгын давхар'
  AND specs->>'Барилгын давхар' ~ '^[0-9]+';

CREATE INDEX IF NOT EXISTS idx_listings_complex_id ON listings (complex_id);
CREATE INDEX IF NOT EXISTS idx_listings_floor ON listings (floor);

