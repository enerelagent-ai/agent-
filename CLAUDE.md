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
 Week 4: Dedup & cleaning (явцад, branch: week4-dedup) — судалгаа ✅, дизайн/код хараахан эхлээгүй. Баталгаажсан баримтууд:
   - Бодит дублей олдсон: 9571622 + 9706500 нэг ижил байр (river plaza 213м² 5 өрөө), ХОЁР ӨӨР утастай (2 агент), үнэ ~1% зөрүүтэй — dedup_hash-д үнэ/утас ороогүй нь зөв гэдгийг батлав (аль нэгийг оруулсан бол алдах байсан)
   - Нэг утас ≠ дублей: нэг дугаар олон өөр объект зардаг (агент/олон хөрөнгөтэй эзэн) — утсыг dedup шалгуур болгож ХЭРЭГЛЭХГҮЙ, харин agent-таних шинж болгон ашиглана
   - Координат найдваргүй: газрын зурган дээр pin тавиагүй зарууд хороооны default цэгтэй ирдэг (ж: 47.91243/106.92175 = СБД Хороо 1 default — 3 өөр барилгын зар ижил координаттай) — exact координат тааруулбал ХУДАЛ дублей үүснэ
   - Дизайны чиглэл: dedup_hash = зөвхөн candidate bucket (хороо түвшний хаяг тул 38k дээр өөр өөр ижил-талбайтай байрууд мөргөлдөнө); шийдвэрлэх логик = bucket доторх pairwise scoring (title/барилгын нэр token similarity, үнийн ойролцоо байдал, зураг, огноо); >95% нарийвчлалыг хэмжихийн тулд labeled тестийн багц (мэдэгдэж буй repost хосууд) эхэлж бүрдүүлэх
   - Scorer ✅ (scraper/scraper/dedup.py): 2 үе шат — are_candidates() blocking (listing_type/property_type/district таарах, өрөө таарах, талбай ±10% band — 51 vs 50 rounding давдаг) + score_pair() (title 0.45 / үнэ 0.35 / зураг 0.08 / огноо 0.12, threshold 0.60). Title normalization: мкв/м²/мк→м2, latin lookalike fold (6-p xopoo→6-р хороо). 14 labeled хос дээр 14/14, margin ≥0.2 (test-ээр хамгаалсан). Labeled багц: tests/fixtures/labeled_pairs.json (2 dup: river plaza + orchlon 51vs50; 12 distinct: same-phone, same-complex, default-pin, generic-title hard negatives). Анхаар: 2 positive-той жижиг багц — жин/threshold-ыг том scrape дээр гарах жинхэнэ хосоор баталгаажуулж байж >95% гэж мэдэгдэнэ; зургийн тоо сул шинж (агентууд өөрсдөө зураг авдаг: 16 vs 8)
 Week 5: Calculations
 Week 6: Dashboard
 Week 7: Integration & testing
 Week 8: Deploy + auth нэмэх
 