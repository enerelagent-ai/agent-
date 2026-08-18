# Investment confidence contract

Formula version: `investment-confidence-v1`

The district investment summary exposes confidence separately from the
investment score. The score ranks districts; confidence describes whether the
underlying inputs are sufficiently numerous, fresh and complete.

## Inputs

- `n_sale` and `n_rent` are evaluated separately; the smaller side limits the
  confidence tier.
- `data_as_of` is the latest real `scraped_at` in that district, not the API
  request time.
- `room_coverage_pct` is the share of active canonical apartment listings with
  a room value.
- `area_coverage_pct` is the share of active canonical sale apartments with an
  area of at least 10 m².
- `price_guard_excluded_pct` is the non-negotiable share rejected by the
  existing yield price guard because price is missing, non-positive, or above
  100 billion MNT. It is not presented as an IQR/model-based outlier metric.

## Tiers

| Tier | Requirements |
|---|---|
| `unavailable` | Either sale or rent sample is below 20 |
| `high` | Both samples ≥100, age ≤2 days, room coverage ≥95%, area coverage ≥80%, price-guard exclusions ≤5% |
| `medium` | Both samples ≥40, age ≤7 days, room coverage ≥90%, area coverage ≥60%, price-guard exclusions ≤10% |
| `low` | Calculation is available but does not clear every medium threshold |

A tier only passes when every requirement in that row passes. This prevents a
large sale sample from hiding a thin rent sample, or high coverage from hiding
stale data.

## Local audit — 2026-08-18

Six districts currently clear the investment calculation's minimum sample.
All six classify as `medium`: samples and coverage are strong, price-guard
exclusions are 0%, but their latest scrape is from 2026-08-13 and therefore
does not meet the two-day `high` freshness requirement.
