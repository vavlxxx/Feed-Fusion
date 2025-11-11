from datetime import timedelta
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    TITLE: str = "Feed Fusion"
    MODE: Literal["TEST", "DEV", "PROD"] = "DEV"
    EMPTY_TEXT: str = "Отсутствует"
    TIMEZONE: int = 5
    PREFERED_HOURS_PERIOD: int = 24

    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_CONTACT: str

    DB_HOST: str
    DB_USER: str
    DB_NAME: str
    TEST_DB_NAME: str = "test_ffusion_db"
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

    REDIS_HOST: str
    REDIS_PORT: int

    @property
    def redis_url(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"

    RABBIT_USER: str
    RABBIT_PASSWORD: str
    RABBIT_HOST: str
    RABBIT_PORT: int
    TELEGRAM_NEWS_QUEUE: str

    @property
    def rabbit_url(self):
        return f"amqp://{self.RABBIT_USER}:{self.RABBIT_PASSWORD}@{self.RABBIT_HOST}:{self.RABBIT_PORT}"

    ES_HOST: str
    ES_PORT: int
    ES_INDEX_NAME: str = "news"
    ES_USE_KNN: bool = False
    ES_RESET_INDEX: bool = True

    @property
    def get_elasticsearch_url(self):
        return f"http://{self.ES_HOST}:{self.ES_PORT}"

    JWT_EXPIRE_DELTA_ACCESS: timedelta = timedelta(minutes=15)
    JWT_EXPIRE_DELTA_REFRESH: timedelta = timedelta(days=30)
    JWT_ALGORITHM: str = "RS256"
    JWT_PRIVATE_KEY: Path = BASE_DIR / "creds" / "jwt-private.pem"
    JWT_PUBLIC_KEY: Path = BASE_DIR / "creds" / "jwt-public.pem"

    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env.template",
            BASE_DIR / ".env",
        ),
        extra="ignore",
    )


settings = Settings()
