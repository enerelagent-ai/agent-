-- 015: verified locations for two Session 0 extractor-exception aliases.
INSERT INTO verified_complex_locations
    (complex_id, district, evidence_text, registry_version)
SELECT c.id, 'Хан-Уул',
       'Session 0 exception manually reviewed: landmark followed by explicit unit',
       'session0-v1'
FROM complexes c
WHERE c.canonical_name = ANY (ARRAY['Romana residence', 'Зайсан шинэ мөрөөдөл'])
ON CONFLICT (complex_id, district, registry_version) DO NOTHING;
