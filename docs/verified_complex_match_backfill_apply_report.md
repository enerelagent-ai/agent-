# Verified complex match pilot — apply report

Applied locally: 2026-08-19 (Asia/Ulaanbaatar)

## Scope

The reviewed dry-run found 922 active legacy assignments eligible under all
Release 3 gates:

- the current versioned extractor agrees with the assigned canonical complex;
- the evidence uses a reviewed alias;
- the relation is `unit`, not `landmark`;
- the complex has an independently verified location;
- the listing passes the district guard or an exact reviewed override.

The apply command used `--expected-count 922`. Any change in live eligibility
would have aborted before a write.

## Result

- Eligible: 922
- Applied and committed in one transaction: 922
- Existing current evidence before apply: 0
- Missing after apply: 0
- Unexpected after apply: 0
- Invalid match state: 0
- Listings with multiple current matches: 0

The script writes `approved` unit evidence with extractor version, exact title
evidence, reviewed alias, confidence, review timestamp, and the policy audit
note `legacy verified-match backfill v1: extractor + verified-location +
district guard`. It does not rewrite `listings.complex_id`.

## Idempotency

A second apply run produced:

```text
eligible=922 prepared=0 already_current=922
applied=0 skipped_current=922; committed
```

The remaining 3,049 unregistered unit assignments and 12 landmark matches were
not applied. They remain outside verified insights pending registry expansion
or human review.

