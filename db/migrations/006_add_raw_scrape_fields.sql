-- 006: Persist raw scrape data that cleaning/extraction may need later.
--
-- Before the full ~38k scrape: anything the parser sees but the DB drops
-- would need a complete re-scrape to recover. specs holds the ad's full
-- key-value spec list (Шал, Тагт, Ашиглалтанд орсон он, ...) whose keys
-- vary by listing type; price_raw keeps the display price text (discount
-- detection: old price + new price); posted_raw keeps the original date
-- text as parse evidence.

ALTER TABLE listings ADD COLUMN IF NOT EXISTS specs JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS price_raw TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS posted_raw TEXT;
