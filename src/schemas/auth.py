from datetime import datetime
from enum import Enum
from typing import Annotated

from fastapi import Form
from pydantic import EmailStr

from src.schemas.base import BaseDTO


class UserLoginDTO(BaseDTO):
    username: str
    password: str


class UserRegisterDTO(UserLoginDTO):
    username: str
    password: str


class UserAddDTO(BaseDTO):
    username: str
    hashed_password: str


class UserDTO(BaseDTO):
    id: int
    username: str
    first_name: str | None
    last_name: str | None
    email: EmailStr | None


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
