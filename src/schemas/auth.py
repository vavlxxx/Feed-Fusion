from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import Form
from pydantic import model_validator

from src.schemas.base import BaseDTO


class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class UserLoginDTO(BaseDTO):
    username: str
    password: str


class UserRegisterDTO(UserLoginDTO):
    username: str
    password: str


class UserAddDTO(BaseDTO):
    username: str
    hashed_password: str
    role: UserRole


class UserDTO(BaseDTO):
    id: int
    username: str
    role: UserRole = UserRole.CUSTOMER
    telegram_id: str | None
    first_name: str | None
    last_name: str | None


class UserUpdateDTO(BaseDTO):
    first_name: str | None = None
    last_name: str | None = None
    telegram_id: str | None = None

    @model_validator(mode="after")
    def validate_all_fields_are_providen(self):
        values = tuple(self.model_dump().values())
        if all(map(lambda val: val is None, values)):
            raise ValueError("provide at least one non-empty field")
        return self


class UserWithPasswordDTO(UserDTO):
    hashed_password: str


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class CreatedTokenDTO(BaseDTO):
    type: TokenType
    token: str
    expires_at: datetime


class TokenAddDTO(BaseDTO):
    owner_id: int
    type: TokenType
    hashed_data: str
    expires_at: datetime


class TokenDTO(TokenAddDTO):
    id: int


class TokenResponseDTO(BaseDTO):
    access_token: str
    refresh_token: str
    type: str = "Bearer"


LoginData = Annotated[UserLoginDTO, Form()]
RegisterData = Annotated[UserRegisterDTO, Form()]
