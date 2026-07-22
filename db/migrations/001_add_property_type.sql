-- 001: Add property category columns to listings.
--
-- Price-per-sqm comparisons are only meaningful within one property type
-- (apartment vs office vs warehouse ...), so the category from the ad
-- page's breadcrumb must be stored on each listing. Values are the raw
-- Unegui breadcrumb category; note the site's slugs/names differ between
-- sale and rent for the same physical type, so queries must group by
-- (listing type, property_type). Subtype is optional; for apartments it
-- carries the room count (e.g. "3 өрөө").

ALTER TABLE listings ADD COLUMN IF NOT EXISTS property_type TEXT;
ALTER TABLE listings ADD COLUMN IF NOT EXISTS property_subtype TEXT;

CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings (property_type);
