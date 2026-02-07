from typing import Annotated

from fastapi import Depends, Query

from src.schemas.base import BaseDTO


class PaginationParamsDTO(BaseDTO):
    # page: Annotated[int, Query(1, ge=1)]
    limit: Annotated[int, Query(None, ge=1, le=15)]

    # @property
    # def offset(self) -> int:
    #     return (self.page - 1) * self.limit


def get_pagination_params(
    # page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=15,
            description="Максимальное количество новостей на одной странице",
        ),
    ] = 9,
) -> PaginationParamsDTO:
    return PaginationParamsDTO(
        # page=page,
        limit=limit,
    )


PaginationDep = Annotated[PaginationParamsDTO, Depends(get_pagination_params)]
