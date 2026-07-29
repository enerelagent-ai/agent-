# UI/UX Дизайны спецификаци (жишиг баримт)

Эх сурвалж: хэрэглэгчийн өгсөн "premium enterprise SaaS" дизайны тодорхойлолт (Stripe/Linear/Vercel/Notion маягийн). Энэ баримт нь дизайны **зорилтот загвар**, гэхдээ хэрэгжvvлэлт нь эрсдэл/өгөгдлийн бэлэн байдлаар vе шаттай явна.

## A. Одоо хийх (өгөгдөл шаардахгvй)
- Өнгө схем (#0B1739 хар цэнхэр sidebar, #4F46E5 indigo accent, цагаан background), rounded card, зай зохион байгуулалт — одоо байгаа Dashboard-д хэрэглэх
- Investment Calculator (Purchase Price/Rent/Loan оруулаад Yield/ROI/Cash Flow/Payback тооцоолох) — цэвэр томьёо, scrape өгөгдөл шаардахгvй

## B. Одоо байгаа өгөгдлөөр, нэмэлт ажилтай
- Market Analysis хуудас (дvvргийн эрэмбэ, vнийн харьцуулалт) — Week 5 өгөгдлийг дахин зохион байгуулах
- Listings бvтэн data grid хуудас (одоо байгаа filter-ийг өргөтгөх)
- Reports (PDF/Excel export) — pdf/xlsx skill ашиглаж болно

## C. Week 7 (scheduling) дуусахыг хvлээх ёстой
- Notifications (шинэ зар, vнэ өөрчлөгдсөн) — давтан scrape хийж харьцуулах механизм шаардана
- Price History chart (олон цэгтэй бодит trend) — одоогоор ганц цэгтэй, цаг хугацаанд өөрөө баяжина

## D. Зориудаар хойшлогдсон (V2.0, geocoding шаардсан тул) — БҮҮ БАР
- Газрын зураг, Heatmap, Property Pins
- Хамгийн ойр сургууль/эмнэлэг/автобус
- Шалтгаан: олон зарын координат нь бодит биш, зөвхөн хорооны default пин (Week 4-т олсон)

## E. Шалгах шаардлагатай (хэрэгжvvлэхийн өмнө)
- "Давхар" (Floor), "Баригдсан он" (Year Built) талбарууд parser-ийн key-value dict дотор хэр бvрэн бvртгэгдсэнийг шалгах, дараа нь л шvvлт барих

## Хэрэгжvvлэх дараалал (санал)
1. A-хэсэг: одоо байгаа Dashboard-ыг энэ өнгө/загвараар шинэчлэх
2. A-хэсэг: Investment Calculator нэмэх
3. B-хэсэг: Market Analysis, Listings бvтэн хуудас, Reports
4. C-хэсэг: Week 7 дуусмагц Notifications, Price History
5. D-хэсэг: Хэзээ ч биш, эсвэл V2.0-д geocoding шийдвэрлэгдсэний дараа
