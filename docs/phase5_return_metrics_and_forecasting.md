# Phase 5 — Өгөөжийн хэмжүүр ба үнийн таамаглалын бэлэн байдал

## Шийдвэрийн хураангуй

- Одоогийн `gross_rental_yield_pct` бол **зарын дундаж дээр суурилсан нийт түрээсийн өгөөж**. Энэ нь цэвэр ашиг, cap rate эсвэл санхүүжилттэй ROI биш.
- API нийцтэй байдлын төлөө `roi_pct`-ийг одоохондоо ижил утгатай alias хэвээр үлдээнэ. Шинэ дэлгэц, тайлбарт “gross rental yield” гэж нэрлэнэ; `roi_pct`-д өөр томьёог чимээгүй оноохгүй.
- Cap rate, cash-on-cash return, DSCR, IRR-ийг одоогийн өгөгдлөөр найдвартай тооцох боломжгүй. Шаардлагатай бодит зардал, сул зогсолт, зээл болон мөнгөн урсгалын өгөгдлийг доор тодорхойлов.
- Өдөр тутмын scraper амжилттай дуусах бүрд `price_history` snapshot хийнэ. Ижил өдөр дахин ажиллуулахад мөр давхардахгүй, тухайн өдрийн утгыг upsert хийнэ.
- Одоо forecast харуулахгүй. Хугацааны цуваа болон backtest-ийн босгыг хангаагүй үед таамаг мэт харагдах тоо зохиохгүй.

## 1. Одоогийн тооцоо яг юу вэ?

Room-level тооцоо нь ижил `district + property_subtype + rooms` бүлгийн идэвхтэй, canonical орон сууцны зарах болон түрээслэх заруудыг тааруулна:

```text
дундаж жилийн түрээс = дундаж сарын түрээс × 12
gross rental yield (%) = дундаж жилийн түрээс / дундаж зарах үнэ × 100
payback years = дундаж зарах үнэ / дундаж жилийн түрээс
```

District summary-д room бүлгүүдийг энгийнээр дундажлахгүй. Зарах үнийг `n_sale`, түрээсийг `n_rent`-ээр тус тус жинлээд district-ийн yield-ийг дахин бодно. Зарах болон түрээслэх тал тус бүр 20-оос цөөн зар байвал district-ийг ranking-ээс хасна.

### Хамрахгүй зүйлс

Энэ хэмжүүр:

- зарлагдсан үнэ, зарлагдсан сарын түрээс ашигладаг; бодит хэлцэл, бодит гэрээний үнэ биш;
- сул зогсолт, төлбөр тасалдал, СӨХ, менежмент, засвар, даатгал, татвар, өмчлөгчийн төлөх хэрэглээний зардлыг хасдаггүй;
- урьдчилгаа, зээлийн хүү, үндсэн төлбөр, хаалтын болон засварын анхны зардлыг тооцдоггүй;
- үнийн өсөлт, борлуулах зардал, татвар, мөнгөний цаг хугацааны үнэ цэнийг тооцдоггүй.

Иймээс `roi_pct == gross_rental_yield_pct` нь зөвхөн одоогийн backward-compatible alias. Хэрэглэгчид “цэвэр ROI” гэж ойлгуулж болохгүй.

## 2. Дараагийн өгөөжийн хэмжүүрүүд

### Cap rate

```text
effective gross income = scheduled rent + other income - vacancy/credit loss
NOI = effective gross income - property operating expenses
cap rate (%) = stabilized annual NOI / acquisition price (эсвэл current market value) × 100
```

Cap rate нь NOI-г үл хөдлөхийн үнэд харьцуулдаг. NOI-д үйл ажиллагааны орлого, зардал орно; ердийн тодорхойлолтоор зээлийн төлбөр, хүү, элэгдэл нь property operating expense биш. Acquisition price болон current market value-ийн аль нэгийг сонгосноо API/дэлгэц дээр заавал нэрлэнэ.

Шаардлагатай шинэ өгөгдөл: бодит гэрээт түрээс, occupancy/vacancy, төлбөр тасалдал, бусад орлого, СӨХ, менежмент, урсгал засвар, даатгал, үл хөдлөхийн татвар, өмчлөгчийн төлөх хэрэглээ, тогтмол reserve. Эдгээргүйгээр gross yield-д таамагласан хувь хасаад “cap rate” гэж нэрлэхгүй.

### Cash-on-cash return

```text
annual pre-tax cash flow = NOI - annual debt service - recurring capital outlay
cash-on-cash (%) = annual pre-tax cash flow / initial cash invested × 100
```

Шаардлагатай шинэ өгөгдөл: дээрх NOI-ийн бүх оролт, урьдчилгаа, худалдан авалтын/хаалтын зардал, анхны засвар, зээлийн дүн, хүү, хугацаа, amortization, debt service. Энэ нь хэрэглэгч бүрийн санхүүжилтээс хамаардаг тул дараагийн calculator-д user input хэлбэрээр авах нь зөв.

### DSCR

```text
DSCR = NOI / annual debt service
```

Зээлийн эргэн төлөлтийн даацыг харуулна. NOI болон бодит зээлийн жилийн төлбөргүй үед тооцохгүй.

### Total return ба IRR

Эдгээр нь эзэмшсэн хугацааны түрээсийн цэвэр cash flow, худалдан авалт/борлуулалтын зардал, эцсийн борлуулалтын орлого, мөн урсгал бүрийн огноог шаарддаг. `price_history`-ийн зарын дундаж үнэ нь нэг хөрөнгийн бодит борлуулалтын cash flow биш учраас дангаараа IRR болгоход хангалтгүй.

| Хэмжүүр | Одоо тооцож болох эсэх | Гол дутуу өгөгдөл |
|---|---:|---|
| Gross rental yield | Тийм | Бодит хэлцлийн үнэ байвал чанар нэмэгдэнэ |
| Cap rate | Үгүй | Vacancy, бодит орлого, operating expenses |
| Cash-on-cash | Үгүй | NOI, зээл, урьдчилгаа, анхны хөрөнгө |
| DSCR | Үгүй | NOI, annual debt service |
| Total return / IRR | Үгүй | Хугацаатай бодит cash flows, exit value/costs |

## 3. `price_history` ба өдөр тутмын snapshot

`.github/workflows/daily-scrape.yml` өдөр бүр scraper ажиллуулдаг. Pipeline хоёр ангиллын scrape-ийг дуусгаж browser-оо хаасны дараа `snapshot_market_prices_conn()`-ийг нэг удаа дуудна. Snapshot нь canonical, идэвхтэй заруудыг `snapshot_date + listing_type + property_type + district` түвшинд хадгална.

- Нэг өдөр дахин ажиллавал unique key дээр upsert хийнэ.
- Дараагийн өдөр шинэ generation нэмэгдэнэ.
- Scrape бүхэлдээ hard failure болсон бол snapshot хүрэхгүй; хэсэг зарын алдаа pipeline-д бүртгэгдсэн ч тухайн үед амжилттай хадгалагдсан зах зээлийн төлөв snapshot-д орно.
- Workflow ажиллахгүй өнгөрсөн өдрийг дараа нь зохиомлоор нөхөж бичихгүй.

## 4. Forecast readiness gate

Доорх нь универсал статистикийн хууль биш, энэ төслийн анхны хамгаалалтын босго юм.

1. **0–29 distinct өдөр:** зөвхөн түүхэн цэгүүд харуулна; trend/forecast label хэрэглэхгүй.
2. **30–89 өдөр:** descriptive rolling average болон өөрчлөлтийг туршиж болно; ирээдүйн таамаг нийтлэхгүй.
3. **90+ өдөр:** зөвхөн хангалттай sample-тай тогтвортой segment дээр baseline forecasting prototype болон rolling-origin backtest эхлүүлж болно.
4. **365+ өдөр:** жилийн улирлын шинжийг шалгах боломж анх үүснэ; нэг жилийн дата улирлын нөлөөг батлахад өөрөө хангалттай гэж үзэхгүй.

Prototype production-д орохын өмнө:

- segment бүрт өдөр тутмын `n_listings`-ийн доод босго болон canonical/extraction дүрэм тогтвортой байх;
- raw average-ийн listing composition өөрчлөлтийг жинхэнэ үнийн хөдөлгөөн гэж андуурахгүй байх (эхний хувилбарт district/property type/rooms-аар stratify хийх, цааш hedonic арга үнэлэх);
- rolling-origin backtest ашиглан MAE болон scale-safe алдаа (жишээ нь WAPE)-г хэмжих;
- “маргаашийн үнэ = өнөөдрийн үнэ” naive baseline-аас тогтвортой дээрдэх;
- prediction interval, training cutoff, segment-ийн sample size, backtest error-ийг хэрэглэгчид ил харуулах;
- data drift эсвэл босго алдагдвал forecast-ыг нууж “өгөгдөл хүрэлцэхгүй” гэж харуулах.

Одоогийн `investment_score` нь үнэ ба gross yield-ийн ил тод rank blend болохоос AI prediction биш. Үүнийг forecast confidence болгон дахин ашиглахгүй.

## 5. Эх сурвалж

- Federal Reserve Bank of San Francisco, [Cap Rates and Commercial Property Prices](https://www.frbsf.org/research-and-insights/publications/economic-letter/2011/09/cap-rates-commercial-property-prices/) — cap rate-ийг NOI/property price харьцаагаар тайлбарласан.
- FDIC/OCC, [Interagency Guidance on Reconsiderations of Value](https://www.fdic.gov/news/financial-institution-letters/2023/fil23034a.pdf) — direct capitalization-д stabilized annual NOI-г cap rate-д хуваан value тооцох арга.
- IRS, [Publication 527: Residential Rental Property](https://www.irs.gov/forms-pubs/about-publication-527) — түрээсийн орлогоос тусдаа maintenance, insurance, taxes, interest, management, utilities зэрэг зардлууд байдгийг баримтжуулсан.

Эх сурвалжууд нь нэр томьёо, хамрах хүрээг батална. 30/90/365 өдрийн readiness gate болон validation дүрэм нь дээр дурдсанчлан энэ бүтээгдэхүүний эрсдэлийн шийдвэр юм.
