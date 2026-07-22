-- 005: Add price_negotiable — whether the ad carries "Үнэ тохирно".
--
-- Parsed from the display price text on the ad page. Nullable: NULL means
-- the row was saved before this flag existed (or had no price text) and
-- resolves on the next re-scrape of that ad.

ALTER TABLE listings ADD COLUMN IF NOT EXISTS price_negotiable BOOLEAN;
