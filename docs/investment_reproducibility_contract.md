# Investment reproducibility contract

Formula version: `district-investment-v1`

Every row returned by `/dashboard/investment-summary` includes a
`reproducibility` object:

| Field | Meaning |
|---|---|
| `calculated_at` | UTC time when this response's calculation ran |
| `comparison_group` | Exact grouping and eligibility description |
| `n_sale` / `n_rent` | Included canonical sale and rent samples, separately |
| `median_sale_price` | Median sale price over yield-eligible matched apartment groups |
| `median_rent_price` | Median monthly rent over the corresponding matched groups |
| `formula_version` | Stable identifier for the calculation contract |

The comparison group is:

`district + property_subtype + rooms; apartments only; matched sale/rent; active canonical listings`

`complex_id` is deliberately absent. A regression test divides one synthetic
district across two complexes and verifies that it remains one 20-sale / 20-rent
district comparison group.

The existing top-level averages and yield remain the displayed calculation.
The medians in `reproducibility` are audit anchors, not substitutions for those
weighted averages.
