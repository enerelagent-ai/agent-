# Verified complex insights gate

Release 3 Session 5 changes complex-level analytics from trusting the legacy
`listings.complex_id` pointer to requiring matching evidence in
`listing_complex_matches`.

Required evidence:

- `is_current = true`
- `relation = 'unit'`
- `review_status = 'approved'`
- evidence `complex_id` equals the listing's current `complex_id`

This gate applies to complex price summaries, complex median comparison groups,
and complex-level deal badges. District-level investment calculations and the
marketplace browse/filter contract are unchanged.

Local post-pilot coverage on 2026-08-19:

- verified complex price groups meeting minimum sample size: 7
- verified complexes represented in those groups: 5
- listings with a verified complex comparison: 243
- verified complex-level top deals: 28

Unverified legacy pointers remain visible as ordinary listing metadata but
cannot produce a median, discount percentage, or investment claim.

## Release switch

The backend setting `COMPLEX_INSIGHTS_ENABLED` is the authoritative runtime
gate and defaults to `false`. While false, `/dashboard/complex-prices` returns
no insight rows and dashboard listing responses do not execute or attach
complex deal calculations. Canonical names and `complex_verified` identity
badges remain available because they are data provenance, not an investment
claim. Enable the flag only after migrations 017–018 and the verified evidence
backfill have completed in the target database.
