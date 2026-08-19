# Pending complex match backfill — apply report

Applied locally: 2026-08-19 (Asia/Ulaanbaatar)

The legacy dry-run buckets that were not eligible for verified insights were
backfilled as reviewable evidence without changing `listings.complex_id`:

- unregistered unit matches: 3,049
- landmark matches: 12
- total pending evidence applied: 3,061

Every row retains the matched alias, exact title evidence, extractor version,
relation, confidence, and the original review bucket. All have
`review_status = 'pending'`, `reviewed_at = NULL`, and `is_current = true`.
None can contribute to verified complex analytics.

Post-check:

- missing: 0
- unexpected: 0
- invalid state: 0

Idempotency re-run:

```text
pending=3061 prepared=0 already_current=3061
applied=0 skipped_current=3061; committed
```

The complete current legacy evidence inventory after both backfills is:

| Review status | Relation | Count |
|---|---|---:|
| approved | unit | 922 |
| pending | unit | 3,049 |
| pending | landmark | 12 |
| **Total** |  | **3,983** |

