from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    TITLE: str = "FastAPI Quick Start"
    MODE: Literal["TEST", "DEV", "PROD"] = "TEST"

    DB_HOST: str
    DB_USER: str
    DB_NAME: str
    TEST_DB_NAME: str = "shop"
    DB_PORT: int
    DB_PASSWORD: str

    DB_ECHO: bool = False
    DB_EXPIRE_ON_COMMIT: bool = False
    DB_AUTOFLUSH: bool = False
    DB_AUTOCOMMIT: bool = False

    @property
    def DB_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    NAMING_CONVENTION: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    UVICORN_PORT: int = 8888
    UVICORN_HOST: str = "127.0.0.1"
    UVICORN_RELOAD: bool = True

    GUNICORN_PORT: int = 8888
    GUNICORN_RELOAD: bool = False
    GUNICORN_HOST: str = "0.0.0.0"
    GUNICORN_WORKERS: int = 1
    GUNICORN_TIMEOUT: int = 900
    GUNICORN_WORKERS_CLASS: str = "uvicorn.workers.UvicornWorker"
    GUNICORN_ERROR_LOG: str | None = "-"
    GUNICORN_ACCESS_LOG: str | None = "-"

    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env.template",
            BASE_DIR / ".env",
        ),
        extra="ignore",
    )


settings = Settings()
