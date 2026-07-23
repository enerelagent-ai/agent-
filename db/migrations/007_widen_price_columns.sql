-- 007: Widen price columns from NUMERIC(14,2) to NUMERIC(18,2).
--
-- The full scrape hit real ads with prices >= 10^12 MNT (huge commercial
-- properties or seller garbage), overflowing NUMERIC(14,2) and killing the
-- upsert. Store the raw value (cleaning judges plausibility later, per the
-- Week 4 philosophy). price_per_sqm is generated from price, so it must be
-- dropped and re-created to change the underlying type.

ALTER TABLE listings DROP COLUMN IF EXISTS price_per_sqm;
ALTER TABLE listings ALTER COLUMN price TYPE NUMERIC(18, 2);
ALTER TABLE listings ADD COLUMN price_per_sqm NUMERIC(18, 2) GENERATED ALWAYS AS (
    CASE WHEN area_sqm > 0 THEN ROUND(price / area_sqm, 2) ELSE NULL END
) STORED;
