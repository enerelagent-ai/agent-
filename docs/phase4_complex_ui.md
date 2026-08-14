# Phase 4 — Complex filter and dual deal badges

Хэрэгжүүлсэн огноо: 2026-08-14.

## Backend contract

- `GET /dashboard/complexes`: дор хаяж нэг active listing-тэй canonical
  complex-уудыг нэрээр эрэмбэлж буцаана.
- `GET /dashboard/listings?complex_id=<id>`: exact foreign-key filter.
- District deal query одоо `complex_id`-г хамт буцаадаг тул “Хямд боломж”
  tab дээр complex filter pagination-аас өмнө зөв үйлчилнэ.
- Listing-ийн `complex_name` нь complex deal-ийн 20 мөрийн босго даваагүй
  үед ч `complexes` хүснэгтээс ирнэ. Ингэснээр filter option, DB canonical
  name, listing мөр/detail modal гурав яг нэг нэр харуулна.
- Dashboard browse одоо `is_active=true` мөрөөр хязгаарлагдана.

## Frontend

- Шүүлтэд **Хотхон** dropdown нэмэгдсэн; option-уудыг backend canonical
  complex endpoint-оос авна.
- Listing мөрөнд canonical complex нэр district-ийн өмнө харагдана.
- Хоёр independent badge зэрэг харагдана:
  - ногоон `Дүүргээс ↓ X%` — district+rooms, 10%-ийн threshold;
  - цэнхэр `Хотхоноос ↓ X%` — complex+transaction+property type,
    20%-ийн threshold.
- Аль нэг comparison байхгүй бол нөгөөг нуухгүй.
- Detail modal-д district болон complex price/m² comparison тусдаа card,
  тусдаа median/sample size/review warning-тай.
- Complex comparison байхгүй үед “хотхон баталгаажаагүй” болон “20 ижил
  төрлийн зар хүрээгүй” төлвийг ялгаж тайлбарлана.

## Баталгаажуулалт

- Next.js production build: passed
- TypeScript `tsc --noEmit`: passed
- Backend: 5 passed (1 dependency deprecation warning)
- Analytics: 86 passed
- Integration test нь dropdown болон filtered listing response ижил
  canonical name ашиглаж байгааг батална.

Phase 4 дууссанаар төлөвлөгөөний complex extraction → normalized DB →
complex analytics → dual-badge/filter урсгал end-to-end болсон.
