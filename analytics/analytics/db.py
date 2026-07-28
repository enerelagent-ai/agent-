"""Small shared DB connection helper used across this package."""


def normalize_dsn(dsn: str) -> str:
    """Accept both plain libpq URLs and SQLAlchemy-style postgresql+psycopg2:// URLs."""
    return dsn.replace("postgresql+psycopg2://", "postgresql://", 1)
