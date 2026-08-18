# Хотхон assignment dry-run re-extract тайлан (v2 — human label-д тулгуурлав)

Vvсгэсэн: 2026-08-17T09:31:51.138146+00:00

**Анхаар**: dry-run — ямар ч мөр өөрчлөгдөөгvй. Bucket нь extractor-ийн гаралт дангаараа биш, 69 мөрийн гараар баталгаажуулсан label-ийг vндэслэсэн. `confirmed_unlink`-ээс бусад бvх bucket ХVН баталгаажуулах ёстой.

## Тойм (4024 нийт assignment)

| Bucket | Тоо |
|---|---|
| unchanged | 3955 |
| confirmed_unlink | 29 |
| other_unit_manual_review | 27 |
| ambiguous_manual_review | 10 |
| extractor_exception_manual_review | 3 |

## other_unit_manual_review — reassignment нэр дэвшигч (27, батлалт хvлээж байна)

- id=359 district='Хан-Уул' Home Plaza → **Жаргалан** — "Home plaza баруун тал жаргалан хотхонд дуплекс 5 өрөө 241.47 мкв орон сууц"
- id=1797 district='Хан-Уул' Home Plaza → **Нархан** — "Home plaza баруун талд нархан хотхонд 113.0мкв 3 өрөө дуплекс байр"
- id=2883 district='Хан-Уул' Цэнгэлдэх → **SS Garden** — "Худ цэнгэлдэхийн урд тансаг зэрэглэлийн 4 өрөө 155м2 орон сууц /ss garden/"
- id=3398 district='Хан-Уул' Home Plaza → **Нархан** — "Худ home plaza баруун урд нархан хотхонд 150мкв 5 өрөө орон сууц"
- id=5965 district='Хан-Уул' Хүннү 2222 → **Агниста** — "Хүннү 2222-ийн урд агниста хотхонд 315.41м2, 7 өрөө пентхаус"
- id=12371 district='Хан-Уул' Цэнгэлдэх → **Рапид** — "Төв цэнгэлдэхийн хажууд рапид хотхонд 65 м2 2 өрөө орон сууц"
- id=12715 district='Хан-Уул' Japan Town → **SS Garden** — "Худ 120 мянгат japan town-ы хажууд ss garden-д 155м.кв 4 өрөө байр"
- id=19217 district='Хан-Уул' River Garden → **Sky Garden Residence** — "Худ, river garden ард sky garden скай гарден хотхонд намханд 201.33мкв 5 өрөө"
- id=20203 district='Хан-Уул' Home Plaza → **Нархан** — "Худ 15-р хороо home plaza баруун урд нархан хотхонд 150мкв 5 өрөө"
- id=27332 district='Хан-Уул' River Garden → **River Tower** — "River garden зүүн талд river tower 366.7 мкв 8 өрөө орон сууц"
- id=29517 district='Хан-Уул' River Garden → **Modun Town** — "Худ river garden замын эсрэг талд modun town 3 өрөө 94мкв"
- id=29531 district='Хан-Уул' Home Plaza → **Нархан** — "Худ home plaza-ын баруун талд нархан хотхонд 60м2 граштай 2 өрөө байр"
- id=30410 district='Хан-Уул' Home Plaza → **Нархан** — "Худ home plaza баруун нархан хотхонд 251.2мкв хаус"
- id=31330 district='Хан-Уул' River Garden → **River Plaza** — "River garden баруун талд river plaza river office 473.79мкв үйлчилгээний талбай"
- id=32629 district='Хан-Уул' Цэнгэлдэх → **Рапид** — "Цэнгэлдэхийн хажууд рапид хотхонд 2өрөө байр 48мкв"
- id=37868 district='Хан-Уул' Хүннү 2222 → **Агниста** — "Хүннү 2222 урд агниста хотхон 7 өрөө пентхаус 315.41мкв"
- id=58215 district='Хан-Уул' Хүннү 2222 → **Академи 1** — "Худ хүннү-2222 баруун талд академи-1 хотхонд тохижуулсан агуулах"
- id=60265 district='Хан-Уул' Цэнгэлдэх → **Рапид** — "Худ цэнгэлдэхийн урд рапид харш хотхонд 129 мкв 4 өрөө"
- id=61221 district='Хан-Уул' River Garden → **Khan Hills** — "River garden баруун талд khan hills 1 хотхонд 4 өрөө 140.7мкв"
- id=61656 district='Хан-Уул' Хүннү 2222 → **Агниста** — "Хүннү 2222-ийн урд агниста хотхонд 315.41мкв 7 өрөө пентхаус"
- id=61762 district='Хан-Уул' River Garden → **River Plaza** — "River garden ард river plaza 97.5мкв 3 өрөө орон сууц"
- id=61956 district='Хан-Уул' Home Plaza → **Нархан** — "Худ, home plaza баруун урд нархан хотхонд 150мкв 5 өрөө орон сууц"
- id=63380 district='Хан-Уул' Home Plaza → **Нархан** — "Худ 15-р хороо home plaza баруун урд нархан хотхон 150 мкв 5 өрөө"
- id=65396 district='Хан-Уул' River Garden → **Modun Town** — "Худ модун таунд ривер гардены хойно 3 өрөө тавилгатай байр 95мкв"
- id=66728 district='Хан-Уул' Цэнгэлдэх → **Рапид** — "Худ цэнгэлдэхийн зүүн талд рапид харш хороололд бүрэн тавилгатай 2 өрөө 58мкв"
- id=68425 district='Хан-Уул' Хүннү 2222 → **Агниста** — "Худ 17р хороо хүннү 2222ын урд талд агниста хотхонд мастeртай 3 өрөө байр"
- id=69825 district='Хан-Уул' River Garden → **Modun Town** — "River garden зүүн хойно modun town хотхонд 94мкв 3 өрөө байр"

## extractor_exception_manual_review — дутуу alias-аас vvдсэн (3)

- id=29890 district='Хан-Уул' assigned=Цэнгэлдэх санал болгосон=Romana residence одоогийн extractor: relation=landmark canonical=Цэнгэлдэх — "Төв цэнгэлдэхийн хойно романа резиденс 150мкв оффис талбай"
- id=35527 district='Хан-Уул' assigned=Цэнгэлдэх санал болгосон=Рапид одоогийн extractor: relation=landmark canonical=Цэнгэлдэх — "Худ,120 мянгат, цэнгэлдэхийн хажууд хурд хотхонд тавилгатай 2 өрөө 41мкв"
- id=61758 district='Хан-Уул' assigned=Зайсан Green House санал болгосон=Зайсан шинэ мөрөөдөл одоогийн extractor: relation=landmark canonical=Зайсан Green House — "Green house баруун талд humana-тай шинэ мөрөөдөл хотхонд 2 өрөө 67.88м2 орон сууц"

## ambiguous_manual_review — АВТОМАТААР unlink/reassign хийхгvй (10)

- id=2156 district='Хан-Уул' assigned=Цэнгэлдэх тэмдэглэл='galaxy tower (canonical биш)' — "Төв цэнгэлдэх ард galaxy tower оффис үйлчилгээний 240м2 талбай"
- id=4089 district='Хан-Уул' assigned=Цэнгэлдэх тэмдэглэл='pg plaza (canonical биш)' — "Цэнгэлдэхийн урд pg plaza 103мкв оффис"
- id=10135 district='Баянзүрх' assigned=Home Plaza тэмдэглэл='Дvнжингарав (шинэ, canonical биш)' — "Home plaza зүүн талд дүнжингарав хотхонд 4 өрөө 130.21мкв байр"
- id=16070 district='Хан-Уул' assigned=Japan Town тэмдэглэл='royal residence (canonical биш -- Royal garden-ээс өөр нэр)' — "Japan town баруун талд royal residence хотхонд таун хаус 303m2"
- id=23883 district='Хан-Уул' assigned=Цэнгэлдэх тэмдэглэл='нэр дурдаагvй, хэмжээ SS Garden-тэй төстэй ч баталгаагvй' — "Худ цэнгэлдэхийн урд байршилтай 209.72мкв 5 өрөө байр"
- id=28520 district='Хан-Уул' assigned=Гэгээнтэн тэмдэглэл='Оргил шилтгээн (Оргил Стар-тай төстэй ч өөр нэр)' — "Гэгээнтэний урд оргил шилтгээн хотхонд 4 өрөө 88м2"
- id=32083 district='Сүхбаатар' assigned=Sky Tower тэмдэглэл='the down town (canonical биш)' — "Хотын төвд blue sky tower-ийн урд байрлах the down town оффис барилгад 451мкв"
- id=32109 district='Хан-Уул' assigned=Home Plaza тэмдэглэл='forum center (canonical биш, эргэлзээтэй)' — "ХУД home plaza баруун тал forum center 150мkв талбай"
- id=60489 district='Хан-Уул' assigned=Цэнгэлдэх тэмдэглэл='Академи хотхон (Академи 1 эсвэл 2 тодорхойгvй)' — "Худ, төв цэнгэлдэхийн урд академи хотхон 3 өрөө байр 79.98мкв"
- id=64255 district='Баянзүрх' assigned=Home Plaza тэмдэглэл='Дvнжингарав (шинэ, canonical биш)' — "Худ home plaza-ын зүүн талд дүнжингарав хотхонд дулаан зогсоол"

## confirmed_unlink (29) — batalgaажсан landmark, нэр дэвшигчгvй

(бvрэн жагсаалт JSON файлд)
