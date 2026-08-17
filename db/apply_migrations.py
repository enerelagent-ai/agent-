"""Apply pending SQL migrations in filename order with checksum tracking."""

import argparse
import hashlib
import os
from pathlib import Path

import psycopg2

MIGRATIONS_DIR = Path(__file__).with_name("migrations")
LOCK_ID = 8_210_015  # project-scoped PostgreSQL advisory lock


def migration_files() -> list[Path]:
    return sorted(MIGRATIONS_DIR.glob("[0-9][0-9][0-9]_*.sql"))


def checksum(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def apply_migrations(dsn: str) -> list[str]:
    applied_now: list[str] = []
    with psycopg2.connect(dsn.replace("postgresql+psycopg2://", "postgresql://", 1)) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_lock(%s)", (LOCK_ID,))
            try:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        filename TEXT PRIMARY KEY,
                        checksum TEXT NOT NULL,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
                conn.commit()

                for path in migration_files():
                    contents = path.read_bytes()
                    digest = checksum(contents)
                    cur.execute(
                        "SELECT checksum FROM schema_migrations WHERE filename = %s",
                        (path.name,),
                    )
                    existing = cur.fetchone()
                    if existing:
                        if existing[0] != digest:
                            raise RuntimeError(
                                f"applied migration changed on disk: {path.name}"
                            )
                        continue

                    try:
                        cur.execute(contents.decode("utf-8"))
                        cur.execute(
                            "INSERT INTO schema_migrations (filename, checksum) VALUES (%s, %s)",
                            (path.name, digest),
                        )
                        conn.commit()
                    except Exception:
                        conn.rollback()
                        raise
                    applied_now.append(path.name)
            finally:
                cur.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
    return applied_now


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply pending PostgreSQL migrations")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    args = parser.parse_args()
    if not args.database_url:
        parser.error("--database-url or DATABASE_URL is required")
    applied = apply_migrations(args.database_url)
    if applied:
        print(f"applied {len(applied)} migration(s): {', '.join(applied)}")
    else:
        print("database is up to date")


if __name__ == "__main__":
    main()
