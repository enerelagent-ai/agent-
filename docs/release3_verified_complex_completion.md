# Release 3 — Verified Complex Data completion

Code-complete locally on 2026-08-19.

Delivered:

- normalized canonical aliases and versioned listing-match evidence;
- current/history lifecycle with confidence, relation, and review status;
- independently verified district registry and exact listing overrides;
- guarded scraper ingestion and legacy evidence backfills;
- 922 approved local unit matches plus 3,061 pending review records;
- complex analytics restricted to current approved unit evidence;
- verified provenance in listing API and UI;
- read-only queue followed by guarded approve/reject decisions;
- transactional unlink audit for rejected legacy pointers;
- authoritative backend feature switch and production audit/apply workflow.

Local acceptance gates:

- analytics: 116 tests;
- backend: 20 tests;
- scraper: 32 tests;
- Playwright: 6 tests;
- Next.js production build: 15 routes.

Release 3 code is complete, but production rollout is intentionally not done.
Use `v1_5_release_checklist.md`; production audit counts must be reviewed before
any backfill and `COMPLEX_INSIGHTS_ENABLED` must remain false until the
production post-check passes.

Registry expansion remains ongoing data-quality work rather than a blocker for
the marketplace or district-level investment intelligence. Pending unit and
landmark evidence cannot enter complex insights until explicitly reviewed.
