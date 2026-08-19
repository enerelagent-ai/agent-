-- 018: two reviewed Session 0 exception aliases were added to the extractor
-- after their complexes had already been created, so migration 017 could not
-- backfill them from the legacy aliases array. Add them explicitly and fail
-- the migration if either normalized spelling is owned by another complex.

INSERT INTO complex_aliases
    (complex_id, alias, normalized_alias, source)
SELECT c.id, values.alias, values.normalized_alias, 'reviewed'
FROM (VALUES
    ('Romana residence', 'романа резиденс', 'романа резиденс'),
    ('Зайсан шинэ мөрөөдөл', 'шинэ мөрөөдөл', 'шинэ мөрөөдөл')
) AS values(canonical_name, alias, normalized_alias)
JOIN complexes c ON c.canonical_name = values.canonical_name
WHERE NOT EXISTS (
    SELECT 1 FROM complex_aliases a
    WHERE a.normalized_alias = values.normalized_alias
)
ON CONFLICT (normalized_alias) DO NOTHING;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM (VALUES
            ('Romana residence', 'романа резиденс'),
            ('Зайсан шинэ мөрөөдөл', 'шинэ мөрөөдөл')
        ) AS expected(canonical_name, normalized_alias)
        LEFT JOIN complex_aliases a
          ON a.normalized_alias = expected.normalized_alias AND a.is_active
        LEFT JOIN complexes c ON c.id = a.complex_id
        WHERE c.canonical_name IS DISTINCT FROM expected.canonical_name
    ) THEN
        RAISE EXCEPTION 'reviewed complex alias mapping conflict in migration 018';
    END IF;
END $$;

