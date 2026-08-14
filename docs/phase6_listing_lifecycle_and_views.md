# Phase 6 — Зарын lifecycle, сарын хандлага, үзэлтийн тоо

## Хэрэгжүүлсэн шийдэл

Өдөр тутмын incremental crawl нь зөвхөн хамгийн шинэ list page-үүдээр явж, дараалсан known page дээр эрт зогсдог. Тэр partial үр дүнд байхгүй URL-ийг delisted гэж үзвэл хуучин боловч идэвхтэй олон зар буруу хаагдана. Иймээс lifecycle reconcile-ийг тусдаа, долоо хоног бүрийн **бүрэн inventory crawl** болгосон.

`weekly-inventory-reconcile.yml` sale болон rent category тус бүрийг 100 хуудасны дээд хязгаартай crawl хийнэ. Дараах хамгаалалттай:

- bot challenge/network failure гарсан list page strict mode-д бүх reconcile-ийг зогсооно;
- category-ийн natural end (3 дараалсан шинэ URL-гүй page) хүрээгүй, `--pages` limit тулсан бол тухайн inventory-г ашиглахгүй;
- хоосон inventory-г DB helper хүлээж авахгүй;
- verified complete inventory-д харагдсан URL-үүдийг reactivate хийж `delisted_at`-ийг цэвэрлэнэ;
- тухайн sale/rent inventory-д байхгүй, өмнө нь active байсан Unegui URL-үүдийг `is_active=false`, `delisted_at=now()` болгоно;
- мөр устгахгүй.

Detail page дахин scrape хийгдсэн зар `_UPSERT_SQL`-ээр мөн автоматаар reactivate болно.

## Сарын хаагдсан зарын хандлага

`monthly_delisting_trend()` болон `GET /dashboard/delisting-trend` нь:

```sql
GROUP BY date_trunc('month', delisted_at), listing_type, district
```

түвшинд canonical зарын тоог буцаана. `listing_type` болон `district` optional filter-тэй.

Энэ тоог “борлуулсан/түрээслүүлсэн” гэж нэрлэхгүй. List page-с алга болсон зар нь хэлцэл хийгдсэн, эзэн нь татсан, хугацаа дууссан эсвэл дахин нийтэлсэн аль нь ч байж болно. Иймээс UI нэршил нь **хаагдсан/алга болсон зар** байна.

## Үзэлтийн тооны бодит шалгалт

2026-08-14-нд local DB-ийн идэвхтэй Unegui зарын нэгийг Playwright-аар нээж bot challenge давсны дараа дараах DOM батлагдсан:

```html
<span class="counter-views">Үзсэн : 36</span>
```

Иймээс detail parser `span.counter-views`-ээс `view_count` авдаг болсон. Migration 011 нь `listings.view_count INTEGER` нэмнэ; утга нь scrape хийх үеийн хамгийн сүүлийн cumulative counter.

Хязгаарлалт:

- unique user эсэхийг эх сурвалж батлахгүй;
- view нь худалдан авах сонирхол эсвэл хэлцэл биш;
- одоогийн багана хамгийн сүүлийн утгыг хадгална, view-ийн time-series биш;
- view velocity/trend хэрэгтэй бол дараагийн migration-аар `(listing_id, observed_at, view_count)` snapshot table үүсгэх шаардлагатай.
