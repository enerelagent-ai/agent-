# Verified complex match legacy backfill — dry-run

Үүсгэсэн: 2026-08-18T10:03:11.590778+00:00

**READ-ONLY:** DB-д ямар ч match, review эсвэл `complex_id` өөрчлөлт хийгээгүй. Хуучин assignment-ийг үнэн гэж тооцоогүй; extractor + verified registry + district guard гурвыг шинээр шалгасан.

- Legacy assignment шалгасан: 3983
- Өмнө нь байгаа match evidence: 0
- Extractor version: `complex-extractor-v2`

## Ангилал

| Bucket | Тоо | Автомат apply |
|---|---:|---|
| `eligible_approved_pilot` | 922 | Тийм — active pilot |
| `eligible_inactive_history` | 0 | Pilot биш — historical backfill |
| `unit_unregistered_manual_review` | 3049 | Үгүй — human review |
| `district_mismatch_manual_review` | 0 | Үгүй — human review |
| `landmark_manual_review` | 12 | Үгүй — human review |
| `extractor_disagrees_manual_review` | 0 | Үгүй — human review |

## Eligible approved pilot

Эдгээр мөрөнд одоогийн extractor хуучин canonical хотхонтой санал нийлж, relation нь `unit`, alias нь reviewed, хотхон registry-д бүртгэлтэй, district guard давсан. Доорх нь эхний 100 мөр; бүрэн жагсаалт JSON-д байна.

### Active pilot — хотхоноор

| Хотхон | Eligible active зар |
|---|---:|
| Рапид | 215 |
| Sky Garden Residence | 172 |
| River Plaza | 165 |
| Жаргалан | 91 |
| Khan Hills | 68 |
| SS Garden | 47 |
| Romana residence | 41 |
| Modun Town | 39 |
| Нархан | 26 |
| Академи 1 | 22 |
| River Tower | 21 |
| Агниста | 13 |
| Зайсан шинэ мөрөөдөл | 2 |

### Active pilot — эхний 100 мөр

- id=14 **River Plaza** district='Хан-Уул' confidence=0.99 — "Худ river plaza 213мкв 5 өрөө"
- id=69 **Рапид** district='Хан-Уул' confidence=0.99 — "Рапид тавилгатай 2 өрөө байр 47.47мкв"
- id=76 **River Plaza** district='Хан-Уул' confidence=0.99 — "River plaza 5 өрөө 213мк орон сууц"
- id=94 **Рапид** district='Хан-Уул' confidence=0.99 — "Хурд рапид стадион төв цэнгэлдэх хүрээлэнд 42м2 1 өрөө"
- id=151 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо рапид харш хороололд 31мкв 1 өрөө байр"
- id=164 **Рапид** district='Хан-Уул' confidence=0.99 — "Рапид 1өрөө"
- id=178 **River Plaza** district='Хан-Уул' confidence=0.99 — "Худ river plaza 5 өрөө 213мк орон сууц"
- id=288 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Худ 8-р хороо жаргалантын аманд жаргалант виллад 2 давхар хаус 258м2 5 өрөө"
- id=359 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Home plaza баруун тал жаргалан хотхонд дуплекс 5 өрөө 241.47 мкв орон сууц"
- id=409 **River Plaza** district='Хан-Уул' confidence=0.99 — "River plaza-д 213 мкв 5 өрөө"
- id=410 **River Plaza** district='Хан-Уул' confidence=0.99 — "River plaza-д 213 мкв 5 өрөө"
- id=463 **Рапид** district='Хан-Уул' confidence=0.99 — "Рапид хороололд 1 өрөө байр 30.34м2"
- id=599 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ 17-р хороо, skygarden хотхон 174,64 мкв мастертай 5 өрөө орон сууц"
- id=682 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Худ 20-р хороо лавай захын зүүн хойно байрлах жаргалан хотхонд 56мкв 2 өрөө"
- id=703 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-хороо хурд хороолол 1 өрөө 31 мк"
- id=750 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ 17-р хороо ханхиллс хотхонд мастертай 3 өрөө 106мкв байр"
- id=764 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ 17-хороо хан хиллс хотхонд 106мкв 3 өрөө"
- id=782 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо рапид харш хотхонд 125.24мкв 4 өрөө"
- id=808 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 120 мянгат рапид харш хотхонд 129м2 4 өрөө байр"
- id=830 **Рапид** district='Хан-Уул' confidence=0.99 — "Рапид харш хороололд 31.28мкв 1 өрөө"
- id=831 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residenceд 243.78мк 4 өрөө байр"
- id=838 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky Garden Residence өндөр зэрэглэлийн хотхонд 4 өрөө байр 158.85мкв"
- id=885 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence-д 243.78 мкв, 4 өрөө тансаг орон сууц"
- id=973 **River Tower** district='Хан-Уул' confidence=0.99 — "Худ 17 хороо river tower үйлчилгээний талбай"
- id=1014 **River Plaza** district='Хан-Уул' confidence=0.99 — "Худ, 17-р хороо, river plaza-д 30 мкв үйлчилгээний талбай"
- id=1029 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ sky garden residence-д 4 өрөө 159м2 орон сууц"
- id=1090 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо хурд хороололд 4 өрөө 129мкв байр"
- id=1097 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence-д 243.78мкв 4 өрөө байр"
- id=1103 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ хурд рапид 2 өрөө байр 58.06мкв"
- id=1133 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence-д 4 өрөө 165.23мкв байр"
- id=1190 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ рапид харшид 2 өрөө байр 58мкв"
- id=1205 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden reaidence-д 159мкв 4 өрөө"
- id=1211 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden 4 өрөө орон сууц 155.5мкв"
- id=1273 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо рапид харш 1 өрөө 37.8м2"
- id=1275 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ рапид харш 68мкв 2 өрөө байр"
- id=1294 **Рапид** district='Хан-Уул' confidence=0.99 — "Хурд рапид хороололд 1 давхрын 1 өрөө 34мкв"
- id=1299 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden 4 өрөө орон сууц 244мкв"
- id=1355 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden 482мкв дуплекс 7 өрөө"
- id=1360 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden хотхон 155 мкв 4 өрөө орон сууц"
- id=1361 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Ханхиллс хотхон 140мкв 4 өрөө"
- id=1369 **River Plaza** district='Хан-Уул' confidence=0.99 — "Ривер плазад 93 мкв үйлчилгээний талбай"
- id=1373 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ маршалын гүүрний хойно sky garden residence 4 өрөө 166 мкв"
- id=1396 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Khankhills хотхон 106мкв 3 өрөө байр"
- id=1407 **River Tower** district='Хан-Уул' confidence=0.99 — "River tower 366mkv 8 өрөө байр"
- id=1459 **Рапид** district='Хан-Уул' confidence=0.99 — "Рапид хурд 21р байр 128мкв 4 өрөө"
- id=1466 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ хан хиллс 1 хотхонд 106 мкв 3 өрөө"
- id=1509 **River Tower** district='Хан-Уул' confidence=0.99 — "Худ river tower-т үйлчилгээний 56.2мкв талбай"
- id=1512 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ sky garden хотхон шинэ 4 өрөө 166 мкв байр"
- id=1612 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden намханд 174 мк 5 өрөө"
- id=1614 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence 5 өрөө 174,64м2"
- id=1648 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ 17-р хороо sky garden 166мкв 4 өрөө"
- id=1711 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ рапид харш хороололд 31.28 мкв 1 өрөө орон сууц"
- id=1781 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 120мянгат рапид харш хотхонд 31м2 1өрөө байр"
- id=1797 **Нархан** district='Хан-Уул' confidence=0.99 — "Home plaza баруун талд нархан хотхонд 113.0мкв 3 өрөө дуплекс байр"
- id=1888 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden 482мкв пентхаус 7 өрөөтэй"
- id=2003 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ ханхиллс хотхонд 3 өрөө 106 мкв байр"
- id=2012 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ 11-р хороо, хан хиллс хотхонд 106 мкв 3 өрөө орон сууц"
- id=2019 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15 хороо рапид хороололд 1 өрөө 30.34м2 орон сууц"
- id=2022 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо рапид хороололд 1 өрөө орон сууц"
- id=2089 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо рапид_харш хороололд 1 өрөө орон сууц 31.28m2"
- id=2179 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence хотхонд 4 өрөө 165.23m2"
- id=2187 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 120 рапид харш хотхонд 129мкв 4 өрөө байр"
- id=2237 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence пентхаус 379.12мкв 5 өрөө"
- id=2238 **River Tower** district='Хан-Уул' confidence=0.99 — "River tower 366,7мкв 8 өрөө"
- id=2243 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ sky garden хотхон 166 мкв 4 өрөө орон сууц"
- id=2277 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden хотхонд 155мкв 4 өрөө"
- id=2354 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence пентхаус 379,12мкв 5 өрөө"
- id=2390 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden-д пентхаус 8 өрөө 482 мкв"
- id=2407 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Хан хиллс хотхонд 3 өрөө орон сууц 106м2"
- id=2408 **Академи 1** district='Хан-Уул' confidence=0.99 — "Академи 1 хотхонд 70 мкв 3 өрөө"
- id=2428 **SS Garden** district='Хан-Уул' confidence=0.99 — "Хотын төвд тансаг зэрэглэлийн ss gardend 4 өрөө 155m2"
- id=2451 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ 17-р хороо sky_garden_residence хотхонд 5 өрөө байр 201m2"
- id=2452 **SS Garden** district='Хан-Уул' confidence=0.99 — "Худ ss garden хотхонд 4 өрөө орон сууц 155мкв"
- id=2548 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden penthouse 7 өрөө 380мкв"
- id=2624 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden residence 4 өрөө байр 159мкв"
- id=2625 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Жаргалант гарден хотхонд бүрэн цутгамал хаус"
- id=2749 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ khan hills-2 хотхонд 4 өрөө 170м2"
- id=2807 **River Plaza** district='Хан-Уул' confidence=0.99 — "River plaza 5 өрөө 213м2 байр"
- id=2839 **River Plaza** district='Хан-Уул' confidence=0.99 — "River plaza luxury shopping center 1 давхарт 36мкв талбай"
- id=2883 **SS Garden** district='Хан-Уул' confidence=0.99 — "Худ цэнгэлдэхийн урд тансаг зэрэглэлийн 4 өрөө 155м2 орон сууц /ss garden/"
- id=2884 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden хотхонд 4 өрөө 230.62мкв орон сууц"
- id=2893 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Худ ханхиллс хотхонд 3 өрөө 106мкв орон сууц"
- id=2899 **Romana residence** district='Хан-Уул' confidence=0.99 — "Romana residence-д 77.04 мкв талбайтай оффис"
- id=2982 **SS Garden** district='Хан-Уул' confidence=0.99 — "Ss garden хотхонд тансаг 4 өрөө орон сууц 155мкв"
- id=3066 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden хотхон 159мк 4 өрөө"
- id=3160 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Ханхиллс хотхонд 140.7 мкв 4 өрөө орон сууц"
- id=3365 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Худ sky garden хотхон 165мкв 4 өрөө"
- id=3378 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ 15-р хороо хурд хороолол 2 өрөө 68мкв"
- id=3398 **Нархан** district='Хан-Уул' confidence=0.99 — "Худ home plaza баруун урд нархан хотхонд 150мкв 5 өрөө орон сууц"
- id=3480 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ хурд рапид хороололд бүрэн тавилгатай 32м.кв 1 өрөө"
- id=3557 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Жаргалант гарден хотхоны аппартмент дээр 3 өрөө орон сууц 79.5мкв"
- id=3558 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Жаргалант гарден хотхоны аппартмент дээр 3 өрөө 79,5мкв"
- id=3597 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Жаргалан хотхонд синглэ хаус 260м2"
- id=3632 **Khan Hills** district='Хан-Уул' confidence=0.99 — "Хан хиллс хотхонд 4 өрөө 140.7м2"
- id=3801 **Sky Garden Residence** district='Хан-Уул' confidence=0.99 — "Sky garden хотхонд 4 өрөө 159мкв"
- id=3867 **Академи 1** district='Хан-Уул' confidence=0.99 — "Академи 1 хотхонд 70мкв 3 өрөө"
- id=3904 **Modun Town** district='Хан-Уул' confidence=0.99 — "Худ, модун таун хотхонд 133.7мкв 4 өрөө орон сууц"
- id=3916 **Рапид** district='Хан-Уул' confidence=0.99 — "Худ рапид хороололд 1 өрөө орон сууц 31.28мкв"
- id=4007 **Жаргалан** district='Хан-Уул' confidence=0.99 — "Худ жаргалан хотхонд 4 өрөө 135.1мкв байр"
- id=4018 **Академи 1** district='Хан-Уул' confidence=0.99 — "Худ академи 1 хотхонд 3 өрөө 70мкв байр"

## Manual-review жишээ

### unit_unregistered_manual_review (3049)

- id=61 assigned='Хүннү Плюс' extracted='Хүннү Плюс' relation='unit' district='Хан-Уул' allowed=[] — "Худ хүннү plus хотхонд 166.88мкв 5 өрөө байр"
- id=85 assigned='Зайсан Green House' extracted='Зайсан Green House' relation='unit' district='Хан-Уул' allowed=[] — "Зайсан green house хотхонд 5 өрөө дуплекс 189.0мкв"
- id=161 assigned='River Garden' extracted='River Garden' relation='unit' district='Хан-Уул' allowed=[] — "Худ river garden 2 хотхонд 120мкв 4 өрөө"
- id=171 assigned='River Garden' extracted='River Garden' relation='unit' district='Хан-Уул' allowed=[] — "River garden 2 хотхонд 4 өрөө байр 120м2"
- id=172 assigned='River Garden' extracted='River Garden' relation='unit' district='Хан-Уул' allowed=[] — "River garden-нд 4 өрөө орон сууц"
- id=183 assigned='Time Square' extracted='Time Square' relation='unit' district='Хан-Уул' allowed=[] — "Худ time square-т үйлчилгээний талбай"
- id=219 assigned='Хүннү 2222' extracted='Хүннү 2222' relation='unit' district='Хан-Уул' allowed=[] — "Хүннү 2222 хотхоны 3-р ээлж 2 өрөө 49.95мкв орон сууц"
- id=231 assigned='River Garden' extracted='River Garden' relation='unit' district='Хан-Уул' allowed=[] — "River garden time square хотхоны голд river plaza-д 213мкв 5 өрөө байр"
- id=239 assigned='River Villa' extracted='River Villa' relation='unit' district='Хан-Уул' allowed=[] — "River villa хотхонд 105м² luxury 3 өрөө байр"
- id=248 assigned='Regis Place' extracted='Regis Place' relation='unit' district='Хан-Уул' allowed=[] — "Худ 120мянгат зам дагуу regis place-д 390мкв оффис талбай 192мкв террас"
- id=249 assigned='Гэгээнтэн' extracted='Гэгээнтэн' relation='unit' district='Хан-Уул' allowed=[] — "120 мянгат гэгээнтэн оффист оффис талбай 93.03мкв"
- id=268 assigned='King Tower' extracted='King Tower' relation='unit' district='Хан-Уул' allowed=[] — "Худ 17-р хороо king tower хотхонд 56мкв 2 өрөө орон сууц"
- id=270 assigned='Хүннү Плюс' extracted='Хүннү Плюс' relation='unit' district='Хан-Уул' allowed=[] — "Hunnu plus 166.86 мкв 5 өрөө орон сууц"
- id=278 assigned='Хүннү 2222' extracted='Хүннү 2222' relation='unit' district='Хан-Уул' allowed=[] — "Hunnu2222 mastertai 3 uruu 80м2"
- id=280 assigned='Time Square' extracted='Time Square' relation='unit' district='Хан-Уул' allowed=[] — "Time square хотхон 4өрөө 138,9мкв"
- id=295 assigned='Vega City' extracted='Vega City' relation='unit' district='Хан-Уул' allowed=[] — "Худ vega city хотхонд 3 өрөө 82.9m2 байр"
- id=301 assigned='King Tower' extracted='King Tower' relation='unit' district='Хан-Уул' allowed=[] — "King tower хотхонд террастай шинэ 117мкв тагттай 4 өрөө байр"
- id=356 assigned='Seven Star' extracted='Seven Star' relation='unit' district='Хан-Уул' allowed=[] — "Зайсан , seven star хотхонд 107.66мкв мастертай 3 өрөө орон сууц"
- id=373 assigned='King Tower' extracted='King Tower' relation='unit' district='Хан-Уул' allowed=[] — "Худ king tower хотхонд 4 өрөө 145 мкв орон сууц"
- id=376 assigned='Хүннү 2222' extracted='Хүннү 2222' relation='unit' district='Хан-Уул' allowed=[] — "Худ хүннү 2222-т 4 өрөө 117.67 мкв орон сууц"

### district_mismatch_manual_review (0)


### landmark_manual_review (12)

- id=2156 assigned='Цэнгэлдэх' extracted='Цэнгэлдэх' relation='landmark' district='Хан-Уул' allowed=[] — "Төв цэнгэлдэх ард galaxy tower оффис үйлчилгээний 240м2 талбай"
- id=4089 assigned='Цэнгэлдэх' extracted='Цэнгэлдэх' relation='landmark' district='Хан-Уул' allowed=[] — "Цэнгэлдэхийн урд pg plaza 103мкв оффис"
- id=10135 assigned='Home Plaza' extracted='Home Plaza' relation='landmark' district='Баянзүрх' allowed=[] — "Home plaza зүүн талд дүнжингарав хотхонд 4 өрөө 130.21мкв байр"
- id=16070 assigned='Japan Town' extracted='Japan Town' relation='landmark' district='Хан-Уул' allowed=[] — "Japan town баруун талд royal residence хотхонд таун хаус 303m2"
- id=23883 assigned='Цэнгэлдэх' extracted='Цэнгэлдэх' relation='landmark' district='Хан-Уул' allowed=[] — "Худ цэнгэлдэхийн урд байршилтай 209.72мкв 5 өрөө байр"
- id=24017 assigned='River Garden' extracted='River Garden' relation='landmark' district='Хан-Уул' allowed=[] — "River garden урд захын блок дээр 4 өрөө 120м2 байр"
- id=28520 assigned='Гэгээнтэн' extracted='Гэгээнтэн' relation='landmark' district='Хан-Уул' allowed=[] — "Гэгээнтэний урд оргил шилтгээн хотхонд 4 өрөө 88м2"
- id=32083 assigned='Sky Tower' extracted='Sky Tower' relation='landmark' district='Сүхбаатар' allowed=[] — "Хотын төвд blue sky tower-ийн урд байрлах the down town оффис барилгад 451мкв"
- id=32109 assigned='Home Plaza' extracted='Home Plaza' relation='landmark' district='Хан-Уул' allowed=[] — "ХУД home plaza баруун тал forum center 150мkв талбай"
- id=35527 assigned='Цэнгэлдэх' extracted='Цэнгэлдэх' relation='landmark' district='Хан-Уул' allowed=[] — "Худ,120 мянгат, цэнгэлдэхийн хажууд хурд хотхонд тавилгатай 2 өрөө 41мкв"
- id=60489 assigned='Цэнгэлдэх' extracted='Цэнгэлдэх' relation='landmark' district='Хан-Уул' allowed=[] — "Худ, төв цэнгэлдэхийн урд академи хотхон 3 өрөө байр 79.98мкв"
- id=64255 assigned='Home Plaza' extracted='Home Plaza' relation='landmark' district='Баянзүрх' allowed=[] — "Худ home plaza-ын зүүн талд дүнжингарав хотхонд дулаан зогсоол"

### extractor_disagrees_manual_review (0)

