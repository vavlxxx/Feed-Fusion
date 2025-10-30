from typing import Generic, TypeVar

from sqlalchemy import Row, RowMapping

from src.models.base import Base
from src.schemas.base import BaseDTO

ModelType = TypeVar("ModelType", bound=Base)
SchemaType = TypeVar("SchemaType", bound=BaseDTO)


class DataMapper(Generic[ModelType, SchemaType]):
    model: type[ModelType]
    schema: type[SchemaType]

    @classmethod
    def map_to_domain_entity(
        cls,
        db_model: ModelType | dict | Row | RowMapping,
    ) -> SchemaType:
        return cls.schema.model_validate(db_model)

    @classmethod
    def map_to_persistence_entity(
        cls,
        schema: SchemaType,
    ) -> ModelType:
        return cls.model(**schema.model_dump())
