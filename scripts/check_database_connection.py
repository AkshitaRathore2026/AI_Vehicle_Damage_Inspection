import os
import sys
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings


def mask_url(value: str | None) -> str:
    if not value:
        return "not set"
    return make_url(value).render_as_string(hide_password=True)


def main() -> None:
    env_file_values = dotenv_values(".env")
    terminal_database_url = os.environ.get("DATABASE_URL")
    env_file_database_url = env_file_values.get("DATABASE_URL")

    settings = get_settings()
    url = make_url(settings.database_url)

    print("Database URL sources")
    print(f"  terminal DATABASE_URL: {mask_url(terminal_database_url)}")
    print(f"  .env DATABASE_URL:     {mask_url(env_file_database_url)}")
    print(f"  app is using:          {mask_url(settings.database_url)}")
    print()
    print("Database configuration")
    print(f"  driver:   {url.drivername}")
    print(f"  username: {url.username}")
    print(f"  host:     {url.host}")
    print(f"  port:     {url.port}")
    print(f"  database: {url.database}")

    engine = create_engine(settings.database_url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        print()
        print("Connection failed")
        print(f"  error_type: {exc.__class__.__name__}")
        print(f"  message:    {exc}")
        raise SystemExit(1) from exc

    print()
    print("Connection successful")


if __name__ == "__main__":
    main()
