-- 002: Add listing_type (sale vs rent) to listings.
--
-- Sale and rent prices differ by ~100x, so every price statistic must be
-- computed within one transaction type; queries group by
-- (listing_type, property_type). Nullable because V2 sources (Facebook)
-- may not always make the type determinable; no index since the column
-- alone has only two values and always accompanies other filters.

ALTER TABLE listings ADD COLUMN IF NOT EXISTS listing_type TEXT
    CHECK (listing_type IN ('sale', 'rent'));
