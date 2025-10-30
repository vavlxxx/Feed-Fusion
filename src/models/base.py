from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, declared_attr

from src.models.utils.transform_titles import transform_titles_to_snake_case
from src.config import settings


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = MetaData(naming_convention=settings.NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        title = transform_titles_to_snake_case(cls.__name__)
        return f"{title}s"
