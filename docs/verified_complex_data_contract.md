# Verified Complex Data contract

Release 3 separates three concerns that were previously collapsed into
`listings.complex_id`.

## Canonical identity

`complexes` owns the stable complex identity. `complex_aliases` owns each
reviewed spelling and maps one normalized alias to exactly one complex.
Canonical names and the reviewed aliases from the legacy `complexes.aliases`
array are backfilled by migration 017. The array remains temporarily for
backward compatibility and is not the new source of truth.

Alias sources:

- `canonical`: the complex's canonical name
- `reviewed`: a human-reviewed spelling variant
- `discovered`: a candidate admitted for review, not implicitly trusted

## Match evidence

`listing_complex_matches` records what the extractor observed without
silently asserting that the listing is a unit in that complex:

- `relation`: `unit`, `landmark`, or `unknown`
- `confidence`: extractor confidence from 0 through 1
- `evidence_text` and `source_field`: the text behind the match
- `extractor_version`: makes a result reproducible across extractor changes
- `review_status`: `pending`, `approved`, or `rejected`
- `reviewer_note` / `reviewed_at`: review audit metadata
- `is_current`: separates the current extractor result from retained history

An approved or rejected match must have `reviewed_at`; pending matches must
not. Database constraints enforce these invariants.

## Compatibility boundary

`listings.complex_id` remains the existing fast read pointer used by the
marketplace and analytics. Migration 017 does not populate matches from that
pointer and does not change it. New ingestion writes reviewed-alias evidence
after the listing upsert, in the same transaction. A `unit` match updates the
pointer and receives policy approval only when its complex has an independently
verified location and the listing passes the district guard (or an exact
reviewed listing override). Landmark and unregistered/mismatched candidates
remain pending and unlinked. Re-scraping replaces the current marker without
deleting historical evidence.

Complex-level price statistics and deal badges require a current `unit` match
with `review_status = 'approved'` for the same listing and complex. A legacy
`listings.complex_id` pointer by itself is deliberately insufficient for an
insight. Marketplace browsing may still show/filter the raw canonical pointer;
this gate applies to claims such as complex medians and “cheaper than this
complex” badges.

Listing API responses expose `complex_verified` independently from
`complex_name`. The name may still come from the legacy browse pointer;
`complex_verified = true` requires a current approved unit match for that same
listing and complex. Frontends must use this boolean for a verified badge and
must not infer verification from the presence of a name or a `complex_id`.
