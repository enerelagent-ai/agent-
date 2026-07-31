from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/real_estate"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Unset (the local-dev default) -- see app.api.deps.require_admin --
    # leaves every route open, matching CLAUDE.md's "no auth yet, local
    # single-user tool" status. Setting both in production (Render) is what
    # turns auth on.
    admin_username: str | None = None
    admin_password: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
