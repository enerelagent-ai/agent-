-- Latest source-reported detail-page view count. Unegui renders this as
-- <span class="counter-views">Үзсэн : N</span>. This is a cumulative counter
-- observed at scraped_at, not a unique-user count and not a conversion metric.
ALTER TABLE listings ADD COLUMN IF NOT EXISTS view_count INTEGER;

ALTER TABLE listings DROP CONSTRAINT IF EXISTS ck_listings_view_count_nonnegative;
ALTER TABLE listings ADD CONSTRAINT ck_listings_view_count_nonnegative
    CHECK (view_count IS NULL OR view_count >= 0);
