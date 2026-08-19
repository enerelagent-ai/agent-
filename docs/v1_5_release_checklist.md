# Marketplace + Investment + Verified Complex release checklist

## Release order

1. Merge the release branch after all local suites are green.
2. Keep `COMPLEX_INSIGHTS_ENABLED=false` on Render and
   `MARKETPLACE_V2_ENABLED=false` on Vercel.
3. Run GitHub Actions → **Apply database migrations** against Neon. Confirm
   migrations through `018_add_reviewed_complex_alias_gaps.sql` are applied.
4. Run **Verified complex evidence** in `audit` mode. Download and review both
   artifacts. Production counts may differ from local counts; never copy local
   expected counts blindly.
5. Run `apply-approved` with the reviewed production eligible count, then
   `postcheck-approved` with the same count.
6. Run `apply-pending` with the reviewed production unit/landmark counts, then
   `postcheck-pending`. Any count drift aborts before a write.
7. Deploy Render backend with `COMPLEX_INSIGHTS_ENABLED=false` and Vercel
   frontend with `MARKETPLACE_V2_ENABLED=false`.
8. Run the smoke checks. Then enable `MARKETPLACE_V2_ENABLED=true` on Vercel.
9. Verify approved evidence coverage and complex insight responses, then set
   `COMPLEX_INSIGHTS_ENABLED=true` on Render.
10. Trigger **Daily scrape** once and confirm new reviewed-alias evidence has
    one current match per listing.

Do not deploy the Release 3 backend/scraper before migrations 013–018. Do not
enable complex insights before approved-evidence post-check reports zero
missing, unexpected, invalid, and duplicate-current rows.

## Smoke checks

- `/health` returns `ok`.
- `/sale` contains no rent listings; `/rent` contains no sale listings.
- Search → filter → pagination → listing detail → source listing works.
- Sale/rent badges match the API transaction type.
- `/dashboard` shows investment confidence and reproducibility details.
- `/complex-review` shows pending unit/landmark counts and source evidence.
- A landmark cannot be approved; rejecting a test fixture writes an unlink
  audit row in a non-production test database.
- With complex insights off, `/dashboard/complex-prices` returns `[]`.
- With complex insights on, only current approved unit evidence contributes to
  complex medians and deal badges.
- A same-day price snapshot rerun upserts rather than adds a duplicate.

## Current local verification

- Analytics: 116 tests passed.
- Backend: 20 tests passed (one dependency deprecation warning only).
- Scraper: 32 tests passed.
- Marketplace + review queue Playwright smoke: 6 tests passed.
- Next.js production build and TypeScript validation passed with 15 routes.
- Local evidence inventory: 922 approved unit, 3,049 pending unit, 12 pending
  landmark. These are local counts, not production deployment inputs.

## Rollback

Migrations 013–018 are additive. If deployment fails, set both feature flags
to `false` and roll back the Render/Vercel code versions. Leave added tables,
audit rows, and the migration ledger in place. Never delete production evidence
to roll back UI behaviour. Fix schema problems forward with a new migration.
