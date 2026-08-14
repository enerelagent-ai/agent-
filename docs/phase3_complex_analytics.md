# Phase 3 — Complex average price and opportunity signal

Хэрэгжүүлсэн огноо: 2026-08-14.

## Analytics

### `complex_average_price()`

Canonical `(complex_id, listing_type, property_type)` бүлэг бүрээр:

- `avg_price`, `median_price`
- `avg_price_per_sqm`, `median_price_per_sqm`
- `n_listings`, `n_with_price_per_sqm`

Sale/rent болон apartment/garage/office зэрэг property type-уудыг нэг
complex дотор ч холихгүй. Доорх Phase 0 хамгаалалтыг бүгдийг дахин ашиглана:

- auto-resolved duplicate хасна;
- зөвхөн `is_active`;
- `price_negotiable IS NOT TRUE`;
- 100 тэрбум ₮ plausible ceiling;
- доод тал нь 20 canonical listing.

Mean нь тайлангийн зориулалтаар үлдсэн боловч listing deal comparison нь
outlier-д тэсвэртэй median price/m² ашиглана.

### `complex_deal_percentages()`

Listing-ийн price/m²-г өөрийн complex + transaction + property type-ийн
median price/m²-тай харьцуулна.

- `>=20%` ба `<=50%`: `top_deal`
- `>50%`: `needs_review`
- `<20%`: `not_notable`

Энэ нь district-level 10%-ийн дохионоос тусдаа. Аль нэг нь байхгүй үед нөгөө
нь хэвээр ажиллана; хоёр тоог нийлүүлж зохиомол score үүсгээгүй.

## Backend API

- `GET /dashboard/complex-prices`
- Optional query: `complex_id`
- `/dashboard/listings` шинэ талбарууд:
  `complex_name`, `complex_deal_pct`, `complex_deal_status`,
  `complex_deal_reason`, `complex_n_comparable`,
  `complex_median_price_per_sqm`
- Phase 2-ийн `floor`, `total_floors`, `complex_id` мөн Listing API schema-д
  ил болсон.

Frontend TypeScript contract шинэчлэгдсэн боловч хоёр badge-г дүрслэх UI нь
төлөвлөгөөний Phase 4-т зориудаар үлдсэн.

## Бодит local DB validation

- 20 qualifying `(complex, transaction, property type)` group
- 14 distinct complex босго давсан
- 802 listing complex comparison авсан
- 72 `top_deal`
- 4 `needs_review`

## Тест

- Analytics: 86 passed
- Backend: 4 passed (1 dependency deprecation warning)
- Frontend TypeScript: `tsc --noEmit` passed
- Complex tests нь Phase 0 guard, transaction/property separation, 20%-ийн
  boundary болон thin-group exclusion-ийг хамгаална.

Phase 4-т эдгээр independent district/complex талбарыг хоёр тусдаа badge
болгон харуулж, complex filter dropdown нэмнэ.
