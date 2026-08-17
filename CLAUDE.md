CLAUDE.md — Улаанбаатарын Үл Хөдлөх Хөрөнгийн Аналитик Платформ

Энэ файл нь Claude Code-д зориулсан төслийн байнгын context юм. Session бүрийн эхэнд Claude энэ файлыг уншиж, доорх мэдээллийг санаж ажиллана.

Төслийн зорилго

Үл хөдлөх хөрөнгийн олон эх сурвалжийн (Үнэгүй.мн, Facebook групп) зар мэдээллийг нэгтгэн цуглуулж, зах зээлийн дундаж үнэ, түрээсийн өгөөж, хөрөнгө оруулалтын өгөөжийн харьцаа зэрэг үзүүлэлтийг тооцоолсон веб аналитик платформ бий болгох. Хэрэглэгч энэ дата дээр үндэслэн хөрөнгө оруулалтын шийдвэр гаргана.

Хувилбар 1.0 (✅ deploy хийгдсэн): Үнэгүй.мн scraping, дублей илрүүлэлт, analytics dashboard, auth. Хувилбар 1.5 (✅ код дууссан, release verification шат): хотхон extraction/analytics/filter, lifecycle ба view count, өдөр тутмын price snapshot, бүтэн listings browse, investment calculator, compare shortlist, үнийн тархалт, needs-review queue, dashboard deal notification. Хувилбар 2.0 (дараагийн үе шат, хараахан эхлээгүй): Facebook нэгтгэл, төслийн баяжуулсан мэдээлэл, найдвартай дата бүрдсэний дараах forecast судалгаа.

Tech stack
Backend: FastAPI (Python) — Render дээр deploy хийгдсэн; Basic Auth opt-in (ADMIN_USERNAME/ADMIN_PASSWORD хоёуланг тохируулбал л асдаг, local dev-д унтраалттай — backend/app/api/deps.py:require_admin)
Database: PostgreSQL — local dev: Postgres.app; production: Neon (serverless) — 2 тусдаа, өөр өөр хэмжээтэй өгөгдлийн сан гэдгийг анхаар (доорх "Системийн архитектур" хэсэгт)
Scraper: Playwright (Python) — local dev: launchd (scraper/bin/run_daily_scrape.sh); production: GitHub Actions (.github/workflows/daily-scrape.yml)
Frontend: Next.js — Vercel дээр deploy хийгдсэн; session-cookie login/logout, backend-ийн Basic Auth-тай ADMIN_USERNAME/ADMIN_PASSWORD-аар синхрон (frontend/src/middleware.ts, lib/session.ts)
Version control: GitHub (enerelagent-ai/agent-), gh CLI ашиглан auth хийсэн
Deployment: ✅ Week 8-д хийгдсэн — GitHub (эх код) → Vercel (frontend) + Render (backend) + Neon (DB), 3 тусдаа cloud платформ (decoupled), GitHub-аар дамжин CI/CD-ээр автоматаар шинэчлэгддэг

Системийн архитектур (9 давхарга — файлын зураглал)

Дэд бүтэц (3 тусдаа cloud платформ, decoupled):
| Платформ | Үүрэг | Холбогдох файл |
|---|---|---|
| GitHub | Эх код + өдөр тутмын scrape (GitHub Actions, 03:00 ЭТС) | .github/workflows/daily-scrape.yml |
| Vercel | Frontend (Next.js), Edge Network, auto-deploy | frontend/src/app/, frontend/src/lib/api.ts |
| Render | Backend (FastAPI), бизнес логик, тооцоолол | backend/app/main.py, analytics/analytics/calculations.py |
| Neon | Serverless PostgreSQL (production DB) | db/schema.sql, db/migrations/001…012 |

9 үе шат (өгөгдлийн урсгал: scraper → dedup → DB → analytics → API → frontend → auth → deployment):
1. Scraper — scraper/scraper/main.py, list_pages.py, detail_page.py, browser.py — Unegui.mn-ээс татах, бот-чек даван гарах
2. Parsing/Cleaning — detail_page.py, save.py — HTML → бүтэцтэй Dict, талбар/өрөө parse, dedup_hash үүсгэх
3. Duplicate Detection — analytics/analytics/dedup.py (оноо тооцох), matches.py (дамжлага) — жин: title 0.45 / үнэ 0.35 / зураг 0.08 / огноо 0.12 (жишээ тооцоолол доор Week 4 тэмдэглэлд, ID 76 vs 14, score 0.879)
4. Database — db/schema.sql, db/migrations/001…012 — listings, duplicate_matches, price_history, complexes, lifecycle/view/notification state
5. Analytics — analytics/analytics/calculations.py — дундаж үнэ, түрээсийн өгөөж, ROI (давхардсан заруудыг үргэлж хасна)
6. Backend API — backend/app/main.py, api/router.py, api/routes/*.py, api/deps.py — Pydantic моделоор шалгаж JSON буцаана
7. Frontend — frontend/src/app/, components/*.tsx — API-аас JSON татаж интерактив график/хүснэгт үзүүлнэ
8. Authentication — backend/app/api/deps.py (Basic Auth) + frontend/src/middleware.ts, lib/session.ts (session-cookie login) — хоёул ADMIN_USERNAME/ADMIN_PASSWORD-аар синхрон, тохируулаагүй бол local dev шиг нээлттэй
9. Deployment — .github/workflows/apply-migrations.yml → Render/Vercel deploy; daily-scrape.yml + weekly-inventory-reconcile.yml (production), scraper/bin/run_daily_scrape.sh (local dev fallback)

Анхаар: production (Neon) DB нь local dev (Postgres.app)-ээс өөр, тусдаа, харьцангуй бага өгөгдөлтэй сан — GitHub Actions scrape эхэлснээс хойш аажмаар нөхөгдөж байгаа (жишээ: 2026-07-31-ний байдлаар Сонгинохайрхан local дээр n_sale=484 байхад production дээр n_sale=52). Production дээр тоо баримт баталгаажуулахдаа "жижиг байна" гэдгийг санаарай — алдаа биш.

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
Долоо хоногийн бүтэц (V1.0) — 8/8 долоо хоног дууссан ✅
✅ Суурь бэлтгэл — architecture, GitHub, Claude Code тохиргоо, DB schema (бодит Postgres дээр туршиж баталгаажуулсан)
✅ FastAPI дотоод систем (routes, models, DB холболт)
✅ Playwright scraper (Үнэгүй.мн, дээрх тодорхой хамрах хүрээгээр) — 36,666 зар бүрэн scrape хийгдсэн
✅ Дублей илрүүлэлт, өгөгдөл цэвэрлэгээ
✅ Тооцооллын систем: дундаж үнэ, м.кв үнэ, түрээсийн өгөөж, ROI
✅ Next.js dashboard, хайлт/шүүлт
✅ Нэгтгэл ба туршилт (scheduled scraping)
✅ Deploy (Vercel + Render + Neon), auth (Basic Auth + session login)
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
 Week 6: Dashboard ✅ — KPI/donut/price-trend/district table/listings feed, шүүлт+эрэмбэлэлт, "Хямд боломж" deal-finder (confidence tier: top_deal/needs_review), тохиролцоотой үнийн тооцоолол (estimate_negotiable_price), methodology tooltip, listing detail modal, source линк — бүгд main-д нэгдсэн.
 Week 7: Integration & testing ✅ — scheduled scraping:
   - **Чухал алдаа олж засав**: scraper/scraper/main.py Week 4→5 package-split-ийн дараа эвдэрсэн байсан (`from scraper.matches import match_new_listings` — matches.py analytics/ руу нүүсэн ч scraper-ийн импорт шинэчлэгдээгүй, scraper-ийн .venv-д analytics суулгаагүй байсан тул `python -m scraper.main` огт ажиллахгvй байв). Ямар ч тест scraper.main-г import хийдэггvй байсан тул алдаа нуугдмал байсан. Засвар: analytics-ийг scraper/.venv-д editable dependency болгож суулгав (`pip install -e ../analytics`, requirements.txt-д `-e ../analytics` нэмсэн), импортыг `analytics.matches`-руу шилжүүлсэн. Регресс хамгаалалт: tests/test_main.py (шинэ, import + CLI flag smoke test).
   - --skip-recent-days audit ✅: detail-page дахин татахаас зайлсхийхэд зөв ажилладаг (save.recently_scraped, days цонхоор шалгадаг), гэхдээ list-page явалт өөрөө "аль хэдийн мэдэгдэж буй" зартай хуудсуудыг зогсоох механизмгvй байсан (зөвхөн category-ийн жинхэнэ төгсгөлийг илрvvлдэг stop_after_stale — өдөр тутмын incremental ажиллагаанд хамааралгvй). Шинээр нэмсэн: save.known_urls()/known_urls_conn() (scraped_at-аас vл хамааран URL DB-д байгаа эсэхийг шалгана) + list_pages.collect_ad_urls-д known_urls_checker/stop_after_known параметр (analytical, opt-in) + main.py-д --stop-after-known-pages CLI flag (0 = idle). 3 дараалсан хуудас бvгд аль хэдийн мэдэгдэж буй бол зогсоно. Тест: tests/test_list_pages.py (шинэ, 3 тест, monkeypatch-ээр браузергvйгээр), tests/test_save.py +1 тест. Бодит амьд шалгалтаар (2026-07-29): нэг хуудсанд 60 зар байгааг баталгаажуулсан (өмнө нь тодорхойгvй байсан).
   - Хуваарьт scrape ✅ (2026-07-29, дараа нь Week 8-д GitHub Actions-аар орлуулсан): scraper/bin/run_daily_scrape.sh — macOS-д flock(1) байхгvй тул mkdir-based atomic lock, backend/.env-ээс DATABASE_URL ачаалдаг, scraper/logs/daily_scrape_*.log-д бичдэг. launchd job `ai.enerelagent.unegui-scraper.daily` — өдөр бvр 03:00. Одоо зөвхөн **local dev fallback**, production нь Week 8-ийн GitHub Actions ажиллагаанд шилжсэн (доор).
 Week 8: Deploy + auth ✅ (PR #10 week8-deploy, PR #11 login-redesign — 2026-07-31 main-д нэгдсэн):
   - **Deploy**: Render (backend), Vercel (frontend), Neon (serverless PostgreSQL production DB) — 3 тусдаа cloud платформ, дэлгэрэнгүйг дээрх "Системийн архитектур" хэсгээс үз.
   - **Scheduled scrape**: .github/workflows/daily-scrape.yml — 03:00 ЭТС (`cron: "0 19 * * *"` UTC) GitHub-ийн дэд бүтэц дээр ажилладаг тул компьютер/Postgres.app сэрvvн байх шаардлагагvй болсон (Week 7-ийн мэдэгдэж байсан хязгаарлалт шийдэгдсэн).
   - **Auth**: Эхлээд backend-д opt-in single-admin Basic Auth (ADMIN_USERNAME/ADMIN_PASSWORD тохируулбал л асна — b515481), дараа нь frontend-г ижил login-ээр хаасан same-origin API proxy-гоор (0805609), эцэст нь Basic Auth-ийн browser popup-ыг premium split-screen login хуудас + session-cookie урсгал болгож сайжруулсан, logout товч нэмсэн (3699b0b, d6dad83, 5525c9c). Тохируулаагvй бол local dev шиг бvрэн нээлттэй хэвээр.
   - **Алдаа олж засав** (production Render дээрх ажиллагаанаас): matches.superseded_listing_ids() Render→Neon холболтоор ~50 сек зарцуулж байсныг оношилж (DIAG timing instrumentation-оор), N+1 query pattern (бvлэг тус бvрт тусдаа query) байсныг олж, upfront нэг WHERE id=ANY(%s) query болгож 0.65с→0.199с болгосон (451b4a9, branch: fix-n-plus-1-superseded-query — **main-д хараахан merge хийгдээгvй, PR хvлээгдэж байна**).
   - **/listings pagination tiebreaker**: id-г нэмэлт эрэмбийн шалгуур болгож нэмсэн (90a0a82, main-д нэгдсэн) — Week 7-ийн мэдэгдэж байсан асуудал шийдэгдсэн.

Мэдэгдэж буй асуудлууд (Known issues)

 - **matches.superseded_listing_ids() Render→Neon latency**: root cause олдож (N+1 query pattern, бvлэг тус бvрт тусдаа query), fix хийгдсэн (upfront нэг WHERE id=ANY(%s) query, ~50с→0.2с) — commit 451b4a9, branch `fix-n-plus-1-superseded-query`. **Main-д хараахан merge хийгдээгvй** — PR vvсгэж merge хийх шаардлагатай.
 - deal_percentages()-ийг real DB дээр баталгаажуулах явцад олдсон, ховор тохиолддог per-listing өгөгдлийн чанарын асуудлууд (2026-07-28): (1) өрөөний тоо буруу ангилагдсан ховор тохиолдол — listing-ийн title өөр өрөөний тоо заасан ч rooms талбар өөр байх нь бий (ж: id 17500, гарчигт "5 өрөө" гэсэн ч rooms=2 гэж хадгалагдсан); (2) title/талбай (area) зөрүүтэй ховор тохиолдол, scraper талын area parsing-ийн асуудлаас үүдэлтэй (ж: id 2226, 27067 — гарчигт нэг талбай дурдсан ч хадгалагдсан area өөр). Хоёул тус тусдаа ховор бөгөөд нэгтгэсэн тооцооллыг (aggregate calculations) гажуудуулахгүй байгааг баталгаажуулсан, гэхдээ ирээдүйд хайлт/жагсаалт (search/browse) feature дээр ажиллахад анхаарах зүйл.

Шийдэгдсэн асуудлууд (архивт, лавлагаанд): /listings pagination tiebreaker (90a0a82, main), Хуваарьт scrape-ийн Postgres.app/компьютер сэрvvн байх шаардлага (Week 8 GitHub Actions deploy-ээр production талд бvрэн арилсан).
