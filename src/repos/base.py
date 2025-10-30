from typing import Generic, Sequence

from asyncpg import DataError, UniqueViolationError
from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from src.repos.mappers.base import DataMapper, ModelType, SchemaType
from src.schemas.base import BaseDTO
from src.utils.exceptions import (
    ObjectAlreadyExistsError,
    ObjectNotFoundError,
    ValueOutOfRangeError,
)


class BaseRepo(Generic[ModelType, SchemaType]):
    model: type[ModelType]
    schema: type[SchemaType]
    mapper = DataMapper

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_filtered(self, *filter, **filter_by) -> list[SchemaType]:
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        try:
            result = await self.session.execute(query)
        except DBAPIError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, DataError):
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc
            raise exc
        return [self.schema.model_validate(obj) for obj in result.scalars().all()]

    async def get_all(self) -> list[SchemaType]:
        return await self.get_all_filtered()

    async def get_one_or_none(self, *filter, **filter_by) -> SchemaType | None:
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        try:
            result = await self.session.execute(query)
            obj = result.scalars().one_or_none()
        except DBAPIError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, DataError):
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc
            raise exc

        if obj is None:
            return None
        return self.schema.model_validate(obj)

    async def get_one(self, *filter, **filter_by) -> SchemaType:
        query = select(self.model).filter(*filter).filter_by(**filter_by)
        try:
            result = await self.session.execute(query)
            obj = result.scalar_one()
        except NoResultFound:
            raise ObjectNotFoundError
        except DBAPIError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, DataError):
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc
            raise exc

        return self.schema.model_validate(obj)

    async def add_bulk(self, data: Sequence[BaseDTO]) -> None:
        add_obj_stmt = insert(self.model).values([item.model_dump() for item in data])
        await self.session.execute(add_obj_stmt)

    async def add(self, data: BaseDTO, **params) -> SchemaType:
        add_obj_stmt = (
            insert(self.model)
            .values(**data.model_dump(), **params)
            .returning(self.model)
        )
        try:
            result = await self.session.execute(add_obj_stmt)
        except IntegrityError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, UniqueViolationError):
                raise ObjectAlreadyExistsError from exc
            raise exc

        obj = result.scalars().one()
        return self.schema.model_validate(obj)

    async def get_one_or_add(self, data: BaseDTO, **params) -> SchemaType:
        obj = await self.get_one_or_none(**data.model_dump())
        if obj is None:
            return await self.add(data, **params)
        return self.schema.model_validate(obj)

    async def edit(
        self,
        data: SchemaType,
        exclude_unset=True,
        exclude_fields=None,
        ensure_existence=True,
        *filter,
        **filter_by,
    ) -> None:
        if ensure_existence:
            await self.get_one(*filter, **filter_by)

        exclude_fields = exclude_fields or set()
        to_update = data.model_dump(exclude=exclude_fields, exclude_unset=exclude_unset)
        if not to_update:
            return
        edit_obj_stmt = update(self.model).filter_by(**filter_by).values(**to_update)

        try:
            await self.session.execute(edit_obj_stmt)
        except IntegrityError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, UniqueViolationError):
                raise ObjectAlreadyExistsError from exc
            raise exc
        except DBAPIError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, DataError):
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc
            raise exc

    async def delete(self, ensure_existence=True, *filter, **filter_by) -> None:
        delete_obj_stmt = delete(self.model).filter(*filter).filter_by(**filter_by)
        try:
            result = await self.session.execute(delete_obj_stmt)
        except DBAPIError as exc:
            if exc.orig and isinstance(exc.orig.__cause__, DataError):
                raise ValueOutOfRangeError(detail=exc.orig.__cause__.args[0]) from exc
            raise exc

        if ensure_existence and result.rowcount == 0:
            raise ObjectNotFoundError

    async def delete_all(self) -> None:
        await self.delete()
