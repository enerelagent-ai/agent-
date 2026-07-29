CLAUDE.md — Улаанбаатарын Үл Хөдлөх Хөрөнгийн Аналитик Платформ

Энэ файл нь Claude Code-д зориулсан төслийн байнгын context юм. Session бүрийн эхэнд Claude энэ файлыг уншиж, доорх мэдээллийг санаж ажиллана.

Төслийн зорилго

Үл хөдлөх хөрөнгийн олон эх сурвалжийн (Үнэгүй.мн, Facebook групп) зар мэдээллийг нэгтгэн цуглуулж, зах зээлийн дундаж үнэ, түрээсийн өгөөж, хөрөнгө оруулалтын өгөөжийн харьцаа зэрэг үзүүлэлтийг тооцоолсон веб аналитик платформ бий болгох. Хэрэглэгч энэ дата дээр үндэслэн хөрөнгө оруулалтын шийдвэр гаргана.

Хувилбар 1.0 (одоогийн ажил, 8 долоо хоног): Үнэгүй.мн-с scraping, дублей илрүүлэлт, тооцооллын систем, dashboard. Хувилбар 2.0 (дараагийн 8 долоо хоног): Facebook нэгтгэл, барилгын төслийн мэдээллийн сан, AI-аар санал болгох/үнэлгээ хийх систем, дулааны зураг, мэдэгдлийн систем.

Tech stack
Backend: FastAPI (Python) — одоогоор auth байхгүй (local, single-user tool; deploy хийхийн өмнө нэмнэ)
Database: PostgreSQL (Postgres.app, local dev)
Scraper: Playwright (Python)
Frontend: Next.js
Version control: GitHub (enerelagent-ai/agent-), gh CLI ашиглан auth хийсэн
Deployment: тогтмол ашиглагдах серверт байршуулна (V1.0-ийн эцэст)
Кодын дүрэм / conventions
Python: PEP8, type hints ашиглах, функц бүрт docstring
Commit бүр жижиг, нэг л зорилготой байх; feature бүр тусдаа commit
Тооцооллын логик (үнэ, ROI, түрээсийн өгөөж) бүрт unit test заавал байх
Scraper нь rate-limit/delay-тай (2-3 сек), сайтын ачааллыг хүндэтгэсэн байх ёстой
Нууц түлхүүр, DB нэвтрэх мэдээллийг код дотор бичихгүй — .env ашиглах (.gitignore-т орсон)
Feature branch-аас main руу PR/merge хийж ажиллах (git checkout -b weekN-feature)
Тодорхойгүй/placeholder үнэтэй зар (ж: "Үнэ тохирно" гэсэн текстийн хамт нэрлэсэн бага тоо) — эх сурвалж бүрт (Unegui, Facebook, ирээдүйн бусад) тохиолдоно. Зарчим: (1) placeholder үнийг ХЭЗЭЭ Ч бодит үнэ гэж бүү тооц — тухайн зарын өөрийнх нь тооцоолол (deal_pct гэх мэт) болон бусад зарын харьцуулалтын baseline (group median) хоёрын аль алинд оролцуулахгүй; (2) харин ижил бүлгийн (district+rooms+listing_type+property_type) бодит үнэтэй зарууд дээр үндэслэн тооцоолсон үнэ (estimate) харуулж болно — analytics.estimate_negotiable_price() (analytics/analytics/calculations.py) функцийг дахин ашиглах, эх сурвалж бүрт тусдаа логик бичихгүй; (3) тооцоолсон үнийг үргэлж "ойролцоогоор, батлагдаагvй" гэдгийг тодорхой дурдаж харуулах, бодит үнэтэй адилхан харагдуулахгүй.
Unegui.mn scraper — тодорхой хамрах хүрээ (Week 3)

Зөвхөн эдгээр 2 URL-ээс scrape хийх:

https://www.unegui.mn/l-hdlh/l-hdlh-zarna/ (Үл хөдлөх зарна — худалдах, ~27,587 зар)
https://www.unegui.mn/l-hdlh/l-hdlh-treesllne/ (Үл хөдлөх түрээслүүлнэ, ~11,049 зар)

АНХААР: /new-buildings/ (Шинэ орон сууц) бол тусдаа ангилал — үүнийг scrape ХИЙХГҮЙ.

Зарын хуудасны бүтэц (/adv/{id}_{slug}/):

Спецификаци нь key-value жагсаалт хэлбэртэй (Шал, Тагт, Ашиглалтанд орсон он, Гараж, Цонх, Барилгын давхар, Хаалга, Талбай, Хэдэн давхарт, Төлбөрийн нөхцөл, Цонхны тоо, Барилгын явц, Цахилгаан шаттай эсэх) — талбарууд зарын төрлөөс хамаарч өөр байдаг тул generic key-value parser хэрэглэх, тогтмол field жагсаалт биш
Байршлын координат (lat/lng) нь газрын зургийн зурган URL-д шууд орсон байдаг: .../geo/static/streets/{lng}/{lat}/... — регекс/URL parsing-аар гаргаж авах боломжтой
Утасны дугаар (баталгаажсан): бүтэн дугаар нь далд contacts-dialog (display:none) дотор tel: линкээр raw HTML-д шууд байдаг — "Дугаар харах" товч дарах шаардлагагүй; 13 зар дээр (хувь хүн + байгууллага) нэг ч олон дугаартай тохиолдол гараагүй
Зургууд (баталгаажсан): зөвхөн div.announcement__images доторх img[itemprop=image]-ийн data-full — хуудсанд төстэй зарын ~50 thumbnail байдаг тул container-оор хязгаарлах заавал
Ангилал (баталгаажсан): breadcrumb (schema.org BreadcrumbList) position 3 = зарах/түрээслэх, 4 = үл хөдлөхийн төрөл, 5 = дэд төрөл (орон сууцанд өрөөний тоо); АНХААР — slug нь зарах/түрээслэхэд өөр өөр (oron-suuts-zarna vs oron-suuts) тул бүлэглэхдээ үргэлж (listing_type, property_type) хосоор; URL slug-д огт итгэхгүй (хуучин зарыг дахин ашигласнаас slug худал байж болно, ж: audi-a6 slug-тай орон сууцны зар)
Pagination (баталгаажсан): ?page=N query param, 1-р хуудас параметргүй
Долоо хоногийн бүтэц (V1.0)
✅ Суурь бэлтгэл — architecture, GitHub, Claude Code тохиргоо, DB schema (бодит Postgres дээр туршиж баталгаажуулсан)
✅ FastAPI дотоод систем (routes, models, DB холболт) — баталгаажуулсан, auth Week 8 хүртэл хойшлуулсан
🔄 Playwright scraper (Үнэгүй.мн, дээрх тодорхой хамрах хүрээгээр) — явцад байна
Дублей илрүүлэлт, өгөгдөл цэвэрлэгээ (>95% нарийвчлал зорилт)
Тооцооллын систем: дундаж үнэ, м.кв үнэ, түрээсийн өгөөж, ROI
Next.js dashboard, хайлт/шүүлт
Нэгтгэл ба туршилт
Deploy, аюулгүй байдал, баримт бичиг, auth нэмэх
Claude Code-той ажиллах зарчим
Даалгаврыг өдрийн хэмжээнд задалж өгөх — том context нэг дор өгөхгүй
Нарийн/эрсдэлтэй логик (dedup, тооцоолол, scraper-ийн бодит бүтэц)-ыг эхлээд шалгуулж/төлөвлүүлж, дараа нь бичүүлэх — таамаглал биш баталгаажсан мэдээллээр ажиллах
Feature бүрийн дараа commit хийх, тестээ ажиллуулах, GitHub руу push хийх
Feature шилжихдээ context цэвэрлэх (/clear эсвэл шинэ session)
Их хэмжээний өгөгдөл дээр (жишээ нь 38,000 зар) шууд ажиллуулахгүй — эхлээд бага хэмжээгээр (15-20 жишээ) end-to-end тест хийж баталгаажуулсны дараа л томсгох
Одоогийн статус

(Claude Code-той ажиллах явцад энэ хэсгийг тогтмол шинэчилж, "юу дуусгасан / юу хийж байгаа" гэдгээ тэмдэглэ)

 Week 1: Architecture, GitHub, DB schema — бодит Postgres дээр баталгаажсан
 Week 2: FastAPI backend (schedule-ээс түрүүлж дуусгасан)
 Week 3: Scraper: list-page URL цуглуулалт ✅, detail-page parser ✅ (title/тайлбар/үнэ/байршил/огноо/координат/ангилал/утас/зураг/generic specs — 13 зар дээр live баталгаажсан), DB migration 001-003 (property_type, listing_type, posted_at) applied ✅, DB хадгалалт ✅ (scraper/scraper/save.py — dedup_hash, (source, source_url) upsert, unit test 7/7, 13 зар local Postgres-т end-to-end баталгаажсан), pipeline runner ✅ (scraper/scraper/main.py: --pages/--ads-per-category flag, DATABASE_URL env, 18 зарын batch дээр 0 алдаатай end-to-end баталгаажсан; DB-д 29 зар). Week 3 дууссан — томсгох (бүх ~38k зар, ~өдөр орчим үргэлжилнэ) Week 4-өөс өмнө батлах шийдвэр
 Week 4: Dedup & cleaning (явцад, branch: week4-dedup) — судалгаа ✅, scorer/хадгалалт/цэвэрлэгээ/canonical ✅ (доор). Өргөтгөсөн хамрах хүрээ: docs/week4_data_cleaning_spec.md — дэлгэрэнгүй спецификаци (сайтын 13 категорийн бүрэн жагсаалт, байршлын текст стандартчилал, тайлбараас задлалт, чанарын үнэлгээ); даалгаврыг тэндээс хэсэг тус бүрээр (A/B/C/D) жижиглэн өгнө, бүхлээр нь нэг дор өгөхгүй. Баталгаажсан баримтууд:
   - Бодит дублей олдсон: 9571622 + 9706500 нэг ижил байр (river plaza 213м² 5 өрөө), ХОЁР ӨӨР утастай (2 агент), үнэ ~1% зөрүүтэй — dedup_hash-д үнэ/утас ороогүй нь зөв гэдгийг батлав (аль нэгийг оруулсан бол алдах байсан)
   - Нэг утас ≠ дублей: нэг дугаар олон өөр объект зардаг (агент/олон хөрөнгөтэй эзэн) — утсыг dedup шалгуур болгож ХЭРЭГЛЭХГҮЙ, харин agent-таних шинж болгон ашиглана
   - Координат найдваргүй: газрын зурган дээр pin тавиагүй зарууд хороооны default цэгтэй ирдэг (ж: 47.91243/106.92175 = СБД Хороо 1 default — 3 өөр барилгын зар ижил координаттай) — exact координат тааруулбал ХУДАЛ дублей үүснэ
   - Дизайны чиглэл: dedup_hash = зөвхөн candidate bucket (хороо түвшний хаяг тул 38k дээр өөр өөр ижил-талбайтай байрууд мөргөлдөнө); шийдвэрлэх логик = bucket доторх pairwise scoring (title/барилгын нэр token similarity, үнийн ойролцоо байдал, зураг, огноо); >95% нарийвчлалыг хэмжихийн тулд labeled тестийн багц (мэдэгдэж буй repost хосууд) эхэлж бүрдүүлэх
   - Хадгалалт ✅: duplicate_matches хүснэгт (migration 004; listing_id_a < listing_id_b PK, score, matched_at — audit хийх боломжтой, дахин score-лоход upsert). Pipeline-д холбогдсон ✅: main.py batch upsert-ийн дараа match_new_listings() (scraper/scraper/matches.py — SQL prefilter: listing_type+property_type+district, дараа нь Python дээр are_candidates+score) шинэ заруудыг шалгаж match бичдэг. Бодит баталгаажуулалт: 9706500-г (river plaza twin) жинхэнэ pipeline замаар хадгалахад 14 ↔ 76 match (score 0.879) автоматаар бичигдсэн; DB-д одоо 30 зар, 1 match. Integration test нь rollback-тай тул DB бохирдохгүй (tests/test_matches.py)
   - Цэвэрлэгээ ✅: талбайн тоон утга save-үед parse_area_sqm-ээр аль хэдийн цэвэрлэгддэг ("150 м² м²"→150.0 — Week 3-т хийгдсэн, 33 мөрөнд алдаагүй нь шалгагдсан); price_negotiable BOOLEAN (migration 005) — "Үнэ тохирно"-г price_raw-с parse хийдэг, NULL = тухайн зар дахин scrape хийгдээгүй (дараагийн scrape-д автоматаар бөглөгдөнө)
   - Canonical сонголт ✅: dedup.group_pairs (union-find, transitive бүлэглэлт) + dedup.pick_canonical (бүрэн дата > шинэ posted_at > их id — deterministic) + matches.superseded_listing_ids(cur) → analytics-ийн ХАСАХ ёстой id-ууд (Week 5 тооцоолол бүр үүгээр шүүнэ, давхар тоолохгүй). Бодит DB дээр: river plaza бүлгээс 76 (шинэ, 1.98 тэрбум) үлдэж 14 хасагдана — 33 зараас 32 canonical
   - Scorer ✅ (scraper/scraper/dedup.py): 2 үе шат — are_candidates() blocking (listing_type/property_type/district таарах, өрөө таарах, талбай ±10% band — 51 vs 50 rounding давдаг) + score_pair() (title 0.45 / үнэ 0.35 / зураг 0.08 / огноо 0.12, threshold 0.60). Title normalization: мкв/м²/мк→м2, latin lookalike fold (6-p xopoo→6-р хороо). 14 labeled хос дээр 14/14, margin ≥0.2 (test-ээр хамгаалсан). Labeled багц: tests/fixtures/labeled_pairs.json (2 dup: river plaza + orchlon 51vs50; 12 distinct: same-phone, same-complex, default-pin, generic-title hard negatives). Анхаар: 2 positive-той жижиг багц — жин/threshold-ыг том scrape дээр гарах жинхэнэ хосоор баталгаажуулж байж >95% гэж мэдэгдэнэ; зургийн тоо сул шинж (агентууд өөрсдөө зураг авдаг: 16 vs 8)
 Week 5: Calculations. Бүрэн scrape ✅ дууссан (2026-07-23 шөнө): 36,666 зар (26,378 зарна, 10,288 түрээслүүлнэ), 3 хуудас алдаатай. Замд гарсан 2 асуудал засагдсан: migration 007 (price NUMERIC(18,2) — бодит зар ≥10^12 MNT байдаг), Playwright сүлжээний алдааг (ERR_NETWORK_CHANGED) crash биш log+skip болгосон.
   Confidence tier ✅ (2026-07-27, Week 4 spec A.1): dedup.CANDIDATE_THRESHOLD=0.60 (match гэж бүртгэх), AUTO_RESOLVE_THRESHOLD=0.80 (автоматаар duplicate гэж шийдэх); classify_pair() duplicate/possible_duplicate/distinct 3 төлөвтэй. Баталгаажуулалт: 48,855 бодит match-аас 20-ыг (10×0.60-0.70, 10×0.90+) гараар шалгасан — 0.90+ 10/10 зөв, 0.60-0.70 ердөө ~8/10 зөв. **Чухал засвар**: matches.superseded_listing_ids() өмнө нь БҮХ match (>=0.60)-ыг canonical бүлэглэлтэд ашигладаг байсан нь 36,666-с 13,355 (36%) ЖИНХЭНЭ ялгаатай заруудыг Week 5 тооцооллоос БУРУУГААР хасах байсан; одоо зөвхөн >=0.80 tier ашигладаг (4,312 хасагдана, өмнөх бол 17,667). 0.60-0.80 tier нь matches.possible_duplicate_pairs() — 41,661 хос, Week 6 review queue-д зориулсан, автоматаар юу ч хийхгүй. Test 24/24, labeled fixture 34 хос (14 анхны + 20 бодит масштабаас). Одоо Week 5 тооцоолол эхлэхэд бэлэн: listings WHERE id != ALL(superseded_listing_ids())
   Тооцооллын систем ✅: dedup/matches/calculations.py-г scraper-с тусдаа analytics/ package болгож салгасан (шинэ analytics/analytics/db.py, өөрийн pyproject.toml, тестийн conftest.py — 21/21 тест). average_price_by_group(): дундаж үнэ + м.кв үнэ (listing_type, property_type, district) бүрээр, superseded listing-үүдийг үргэлж хасна. rental_yield_by_district_rooms() (2026-07-27): түрээсийн өгөөж = (дундаж сарын түрээс×12) / дундаж зарах үнэ, (district, property_subtype, rooms) түвшинд яг тохируулж (category-level дундажлахгүй) — учир нь зөвхөн "Орон сууц" ангилалд room count (property_subtype/rooms) бүрэн бөглөгдсөн байдаг (бодит DB-ээр баталгаажсан, бусад 14 ангилалд хоёул NULL). 36 district×өрөө bucket, өгөөж 4.8%-13.4%, payback_years хамт гардаг. yield_category_coverage(): 15 ангилал тус бүрийг calculable эсэхийг мэдээллийн сангаас амьд тоолж, эсэхгүй бол шалтгааныг тэмдэглэдэг (subtype/rooms байхгүй, зөвхөн нэг талд байгаа — түрээслэх л боломжтой, эсвэл Хашаа байшин/Монгол гэр шиг ангиллын нэр өөрөө таарахгүй тохиолдол) — ямар ч ангиллыг ойролцоолж нийлүүлээгүй. investment_summary_by_district() (2026-07-27): rental_yield_by_district_rooms()-г district түвшинд жинтэйгээр (sample size-ээр) нэгтгэж, roi_pct (=gross_rental_yield_pct — зээл/зардлын дата байхгүй тул тусдаа томьёогүй, ил нэрлэсэн alias) болон investment_score (0-100, үнэ+өгөөжийн rank-ийн 50/50 хольц) гаргадаг. n_sale/n_rent < 20 дүүргийг ranking-аас бүрэн хасдаг (жишээ нь Багануур n=1 нь Хан-Уул n=4308-г давахаас сэргийлнэ). Бодит DB: 11 дүүргээс 6 нь босго давж, Сонгинохайрхан (хямд, өгөөж өндөр) тэргүүлж, Хан-Уул (үнэтэй, өгөөж бага) сүүлд. Test 29/29. **Week 5 дууссан** — Week 6 (Dashboard) руу шилжихэд бэлэн.
 Week 6: Dashboard
 Week 7: Integration & testing
 Week 8: Deploy + auth нэмэх

Мэдэгдэж буй асуудлууд (Known issues)

 - backend/app/api/routes/listings.py-ийн /listings endpoint: /dashboard/listings-д олдож засагдсан ижил pagination тогтворгүй байдлын алдаатай (2026-07-28) — ORDER BY зөвхөн scraped_at дээр байдаг тул (batch insert-ийн улмаас олон мөр ижил timestamp-тай) offset хуудаснууд давхцаж болно. Засвар: id-г нэмэлт tiebreaker болгож нэмэх (жишээ нь .order_by(Listing.scraped_at.desc(), Listing.id.desc())) — хараахан хийгдээгүй.
 - matches.superseded_listing_ids(): дуудалт бүрт ~0.7 сек зарцуулдаг (дублей бүлэг тус бүрт тусдаа SQL query хийдэг дизайн). /dashboard/* route бүр энэ функцийг request бүрт дахин тооцоолдог (кэшлэдэггүй). Local single-user хэрэглээнд OK, гэхдээ бодит deployment/traffic-ийн өмнө (Week 8-ийн санаа зовнил) кэшлэх эсвэл урьдчилан тооцоолох (precompute/materialize) шаардлагатай.
 - deal_percentages()-ийг real DB дээр баталгаажуулах явцад олдсон, ховор тохиолддог per-listing өгөгдлийн чанарын асуудлууд (2026-07-28): (1) өрөөний тоо буруу ангилагдсан ховор тохиолдол — listing-ийн title өөр өрөөний тоо заасан ч rooms талбар өөр байх нь бий (ж: id 17500, гарчигт "5 өрөө" гэсэн ч rooms=2 гэж хадгалагдсан); (2) title/талбай (area) зөрүүтэй ховор тохиолдол, scraper талын area parsing-ийн асуудлаас үүдэлтэй (ж: id 2226, 27067 — гарчигт нэг талбай дурдсан ч хадгалагдсан area өөр). Хоёул тус тусдаа ховор бөгөөд нэгтгэсэн тооцооллыг (aggregate calculations) гажуудуулахгүй байгааг баталгаажуулсан, гэхдээ ирээдүйд хайлт/жагсаалт (search/browse) feature дээр ажиллахад анхаарах зүйл.
 