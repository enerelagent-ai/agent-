-- 009: is_active / delisted_at — track listings that disappear from the
-- site (sold, rented, or removed) without deleting their row.
--
-- Soft-delete rather than hard-delete: a listing's history stays queryable
-- for month-over-month closure trend analysis (a future "how many listings
-- closed per district per month" demand/liquidity signal), while every
-- *current* market calculation (average price, yield, deal-finder, and any
-- future complex-level average) must never count a closed listing as live
-- inventory.
--
-- DEFAULT true: every listing scraped so far is presumed still live until a
-- future incremental crawl proves otherwise (a later scraper change sets
-- is_active=false + delisted_at=now() when a previously-known URL drops out
-- of a list-page pass). delisted_at stays NULL for every currently-active
-- row -- it is only ever set at the moment a listing is found gone.

ALTER TABLE listings ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS delisted_at TIMESTAMPTZ;

-- Every market-calculation query in analytics/analytics/calculations.py now
-- filters WHERE is_active, so this index is on the hot path for all of them.
CREATE INDEX IF NOT EXISTS idx_listings_is_active ON listings (is_active);
