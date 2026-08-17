# V1.5 release checklist

## Release order

1. Merge the linear V1.5 branch chain through `v1.5-release-readiness`.
2. Run GitHub Actions → **Apply database migrations** against Neon.
3. Confirm the log ends with migrations through `012_add_notification_state.sql` (or `database is up to date`).
4. Run **Backfill property complexes** once; record its candidate/updated counts.
5. Deploy/redeploy Render backend.
6. Deploy/redeploy Vercel frontend.
7. Trigger **Daily scrape** once; confirm `market snapshot: … price groups recorded`.
8. Keep **Weekly listing inventory reconciliation** scheduled; its first verified complete run establishes real `is_active/delisted_at` changes.

Do not deploy backend/scraper before migrations 009–012: those versions read `is_active`, `complex_id`, `view_count`, and `notification_state`.

## Smoke checks

- `/health` returns `ok`.
- Dashboard loads investment summary with min/median/max distribution.
- `/listings` filters, paginates, opens detail, and compares 2–3 listings.
- `/calculator` changes outputs when vacancy, expenses, or financing inputs change.
- `/notifications` loads, the bell count matches, and **Бүгдийг үзсэн** clears it.
- A detail scrape writes a non-negative `view_count` when Unegui exposes `span.counter-views`.
- A same-day price snapshot rerun upserts rather than adds a duplicate generation.

## Automated verification completed locally

- Migration runner: first run registered 001–012; second run was a no-op.
- Scraper: 25 passed.
- Analytics: full integration suite passed.
- Backend: 6 passed (one dependency deprecation warning only).
- Next.js production build and TypeScript validation passed; `/`, `/listings`, `/calculator`, and `/notifications` compiled.

## Rollback

Migrations 009–012 are additive. If application deployment fails, roll back the Render/Vercel code version and leave the added tables/columns in place. Do not manually delete production data or migration ledger rows. Fix forward with a new numbered migration if a schema correction is required.
