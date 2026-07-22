-- 003: Add posted_at (the ad's own publish date on the source site).
--
-- scraped_at only says when WE fetched the ad; market-freshness analytics
-- (days on market, stale-listing filtering) need the source's publish date.
-- Nullable: the source shows relative dates ("Өнөөдөр 19:05") that may not
-- always be resolvable; the parser keeps the raw string in that case.

ALTER TABLE listings ADD COLUMN IF NOT EXISTS posted_at TIMESTAMPTZ;
