

# Улаанбаатарын Үл Хөдлөх Хөрөнгийн Аналитик Платформ

Үл хөдлөх хөрөнгийн олон эх сурвалжийн (Үнэгүй.мн, Facebook групп) зар мэдээллийг нэгтгэн цуглуулж, зах зээлийн дундаж үнэ, түрээсийн өгөөж, хөрөнгө оруулалтын өгөөжийн харьцаа зэрэг үзүүлэлтийг тооцоолсон веб аналитик платформ.

Дэлгэрэнгүй төслийн context, зорилго, долоо хоногийн төлөвлөгөөг [CLAUDE.md](./CLAUDE.md)-с үзнэ үү.

## Бүтэц (Monorepo)

```
backend/    FastAPI backend, нэвтрэлт баталгаажуулалт
scraper/    Playwright scraper (Python)
frontend/   Next.js dashboard
db/         PostgreSQL schema, migrations
docs/       Архитектур, API баримтжуулалт
```

## Tech stack

- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Scraper:** Playwright (Python)
- **Frontend:** Next.js

## Хөгжүүлэлт эхлүүлэх

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Scraper

```bash
cd scraper
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

`db/schema.sql`-д schema, `db/migrations/`-д migration файлууд байрлана.

Pending migration-уудыг checksum болон advisory lock-той дарааллаар ажиллуулах:

```bash
DATABASE_URL=postgresql://... python db/apply_migrations.py
```

Production release хийхдээ GitHub Actions-ийн **Apply database migrations**
workflow-г эхэлж ажиллуулаад, дараа нь backend/frontend deploy хийнэ. Аль хэдийн
бүртгэгдсэн migration өөрчлөгдсөн бол runner алдаа өгч зогсоно; шинэ өөрчлөлтийг
хуучин SQL-д засварлах биш дараагийн дугаартай migration болгож нэмнэ.

## Нууц мэдээлэл

Нууц түлхүүр, DB нэвтрэх мэдээллийг код дотор бичихгүй. Тус бүрийн хавтсанд `.env` файл ашиглана (`.gitignore`-д орсон).
