from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from src.models.auth import Token, User
from src.repos.base import BaseRepo
from src.repos.mappers.mappers import AuthMapper, TokenMapper
from src.schemas.auth import TokenDTO, UserDTO, UserWithPasswordDTO
from src.utils.exceptions import ObjectNotFoundError


class AuthRepo(BaseRepo[User, UserDTO]):
    model = User
    mapper = AuthMapper

    async def get_user_with_passwd(
        self, **filter_by
    ) -> UserWithPasswordDTO:
        query = select(self.model).filter_by(**filter_by)
        result = await self.session.execute(query)
        try:
            obj = result.scalar_one()
        except NoResultFound:
            raise ObjectNotFoundError
        return UserWithPasswordDTO.model_validate(obj)


class TokenRepo(BaseRepo[Token, TokenDTO]):
    model = Token
    mapper = TokenMapper
