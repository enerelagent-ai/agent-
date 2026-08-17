# Phase 2 — Complex extraction, floor migration, normalized DB

Хэрэгжүүлсэн огноо: 2026-08-14. Branch: `phase1-complex-research`.

## Хэрэгжилт

- `analytics.analytics.complexes`: Unicode/case/punctuation normalization,
  reviewed alias dictionary, Монгол/Англи trigger fallback, numbered
  neighbourhood rejection, `unit` ба `landmark` relation.
- Extractor нь `rooms` болон property category-оос үл хамаарна.
- Known alias дотор unit evidence нь landmark evidence-ээс түрүүлнэ. Жишээ:
  `Хүннү 2222 хажууд Агниста хотхонд...` → `Агниста`.
- Unknown trigger candidate-г audit-д буцаадаг ч production DB-д автоматаар
  complex үүсгэхгүй. Зөвхөн reviewed alias + `unit` relation persistence-д
  орно.

## Accuracy gate

Phase 1-ийн шинэчилсэн privacy-safe fixture дээр:

- Exact canonical recall: `306/320 = 95.625%`
- Confirmed non-complex false positives: `0/12`
- Reused URL-ийн хуучин CSV label сэргээсэн: `0/26`

597 source-unavailable болон 12 insufficient-evidence мөр metric-д ороогүй.
Энэ нь зөвхөн баталгаажсан subset-ийн regression gate бөгөөд бүх зах зээлийн
coverage гэсэн claim биш.

## Migration 010

`db/migrations/010_add_complexes_and_floors.sql`:

- `complexes(id, canonical_name, normalized_name, aliases, timestamps)`
- `listings.complex_id` (`ON DELETE SET NULL`)
- `listings.floor`, `listings.total_floors`
- `specs['Хэдэн давхарт']`, `specs['Барилгын давхар']` backfill
- complex/floor indexes

Local DB үр дүн:

- `floor`: 23,594 мөр
- `total_floors`: 23,594 мөр
- specs-д floor байгаад backfill хийгдээгүй мөр: 0
- canonical complexes: 61
- `complex_id`-тай listings: 4,024 / 44,507

Source data-д `floor > total_floors` 383 мөр байна. Raw specs-тэй ижил
seller/source data тул Phase 2 үүнийг таамгаар зассангүй; future cleaning
rule-ийн тусдаа quality issue болгон үлдээсэн.

## Pipeline ба backfill

- `scraper.save.listing_row_from_parsed()` шинэ scrape бүрт floor-ууд болон
  reviewed complex match гаргана.
- Upsert нь canonical complex-ийг `complexes` хүснэгтэд upsert хийж
  `complex_id` холбоно. Reused URL шинэ title дээр complex evidence-гүй бол
  хуучин `complex_id`-г NULL болгоно.
- `analytics/scripts/backfill_complexes.py` нь default-аар read-only preview;
  зөвхөн `--apply` үед DB update хийдэг.

## Баталгаажуулалт

- Analytics: 82 passed
- Scraper: 18 passed
- Backend: 2 passed (1 dependency deprecation warning)
- Complex metric/backfill tests болон floor parsing/pipeline mapping regression
  test-ээр хамгаалагдсан.

Phase 3-ийн `complex_average_price()` нь `complex_id`-тай canonical listings
дээр Phase 0-ийн `is_active`, duplicate, placeholder/outlier шүүлтийг дахин
ашиглан хэрэгжихэд бэлэн.
