from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings

engine = create_async_engine(
    url=settings.DB_URL,
    echo=settings.DB_ECHO,
)

sessionmaker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=settings.DB_AUTOCOMMIT,
    autoflush=settings.DB_AUTOFLUSH,
    expire_on_commit=settings.DB_EXPIRE_ON_COMMIT,
)

engine_null_pool = create_async_engine(
    url=settings.DB_URL,
    poolclass=NullPool,
)

sessionmaker_null_pool = async_sessionmaker(
    bind=engine_null_pool,
    autocommit=settings.DB_AUTOCOMMIT,
    autoflush=settings.DB_AUTOFLUSH,
    expire_on_commit=settings.DB_EXPIRE_ON_COMMIT,
)
