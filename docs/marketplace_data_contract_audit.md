# Marketplace data contract audit

Audit date: 2026-08-18  
Scope: Release 1, Session 1

## Result

The active listing dataset already has a clean transaction-type contract:

| Check | Result |
|---|---:|
| Active listings | 44,507 |
| `sale` | 30,004 |
| `rent` | 14,503 |
| NULL `listing_type` | 0 |
| Values other than `sale` / `rent` | 0 |
| NULL `property_type` | 0 |
| Sale rows carrying a rent category label | 0 |
| Rent rows carrying a sale category label | 0 |

No data migration is required for the current active dataset.

## Enforced contract

- Marketplace browse accepts only `listing_type=sale` or `listing_type=rent`.
- The transaction filter applies to both recent browse and deal-ranked browse.
- Active listings remain visible in normal browse even when analytics cannot
  classify them and returns `deal_status = null`.
- `needs_review` is an analytics confidence state, not a marketplace
  publication state. It remains browseable but is excluded from the default
  top-deal ranking.
- Inactive and superseded duplicate rows are excluded from dashboard browse.

## Follow-up boundary

The dedicated Marketplace V2 endpoint will carry this contract forward and
replace offset pagination with the planned compound cursor
`(scraped_at DESC, id DESC)`. This audit does not change the legacy
`/listings` endpoint because frontend migration has not happened yet.
