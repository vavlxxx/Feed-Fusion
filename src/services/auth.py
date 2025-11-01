from datetime import datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException, Response
from jwt.exceptions import ExpiredSignatureError

from src.schemas.auth import UserWithPasswordDTO
from src.config import settings
from src.schemas.auth import (
    CreatedTokenDTO,
    LoginData,
    RegisterData,
    TokenAddDTO,
    TokenResponseDTO,
    TokenType,
    UserAddDTO,
    UserDTO,
)
from src.services.base import BaseService
from src.utils.db_tools import DBManager
from src.utils.exceptions import (
    InvalidLoginDataError,
    ObjectExistsError,
    ObjectNotFoundError,
    UserExistsError,
    UserNotFoundError,
)


class AuthService(BaseService):
    def __init__(self, db_manager: DBManager | None = None) -> None:
        super().__init__(db_manager=db_manager)

    def _hash_data(self, password: str) -> str:
        salt = bcrypt.gensalt()
        pwd_bytes: bytes = password.encode(encoding="utf-8")
        hashed_pwd_bytes = bcrypt.hashpw(pwd_bytes, salt)
        return hashed_pwd_bytes.decode(encoding="utf-8")

    def _verify_data(self, password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            password=password.encode(encoding="utf-8"),
            hashed_password=hashed_password.encode(encoding="utf-8"),
        )

    def _generate_token(
        self,
        payload: dict,
        expires_delta: timedelta,
        type: TokenType,
    ) -> CreatedTokenDTO:
        token_data = payload.copy()
        now = datetime.now()
        expires = now + expires_delta
        expires_timestamp = datetime.timestamp(expires)

        token_data["exp"] = expires_timestamp
        token_data["iat"] = datetime.timestamp(now)
        token_data["type"] = type

        token = jwt.encode(
            payload=token_data,
            key=settings.JWT_PRIVATE_KEY.read_text(),
            algorithm=settings.JWT_ALGORITHM,
        )

        return CreatedTokenDTO(
            token=token,
            expires_at=expires,
            type=type,
        )

    def create_access_token(self, payload: dict) -> CreatedTokenDTO:
        return self._generate_token(
            payload=payload,
            expires_delta=settings.JWT_EXPIRE_DELTA_ACCESS,
            type=TokenType.ACCESS,
        )

    def create_refresh_token(self, payload: dict) -> CreatedTokenDTO:
        return self._generate_token(
            payload=payload,
            expires_delta=settings.JWT_EXPIRE_DELTA_REFRESH,
            type=TokenType.REFRESH,
        )

    def decode_token(self, token: str) -> dict:
        try:
            decoded_token = jwt.decode(
                jwt=token,
                key=settings.JWT_PUBLIC_KEY.read_text(),
                algorithms=(settings.JWT_ALGORITHM),
            )
        except ExpiredSignatureError as exc:
            raise HTTPException(status_code=401, detail=str(exc))
        return decoded_token

    async def login_user(
        self, login_data: LoginData, response: Response
    ) -> TokenResponseDTO:
        try:
            user: UserWithPasswordDTO = await self.db.auth.get_user_with_passwd(
                username=login_data.username
            )
        except ObjectNotFoundError as exc:
            raise InvalidLoginDataError from exc

        is_same = self._verify_data(login_data.password, user.hashed_password)
        if not user or not is_same:
            raise InvalidLoginDataError

        return await self.update_tokens(user=user, response=response)

    async def update_tokens(
        self,
        response: Response,
        uid: int | None = None,
        user: UserDTO | UserWithPasswordDTO | None = None,
    ) -> TokenResponseDTO:
        if user is None:
            user = await self.db.auth.get_one(id=uid)
        access_token = self.create_access_token(
            payload={"sub": user.username, "uid": user.id}
        )
        refresh_token = self.create_refresh_token(payload={"sub": f"{user.id}"})

        hashed_refresh_token = self._hash_data(refresh_token.token)

        token_to_update = TokenAddDTO(
            hashed_data=hashed_refresh_token,
            owner_id=user.id,
            **refresh_token.model_dump(exclude={"token"}),
        )
        await self.db.tokens.delete(
            owner_id=user.id,
            ensure_existence=False,
        )
        await self.db.tokens.add(token_to_update)
        await self.db.commit()

        response.set_cookie(
            key="refresh_token",
            value=refresh_token.token,
            httponly=True,
        )

        return TokenResponseDTO(
            access_token=access_token.token,
            refresh_token=refresh_token.token,
        )

    async def register_user(self, register_data: RegisterData) -> UserDTO:
        hashed_password = self._hash_data(register_data.password)
        user_to_add = UserAddDTO(
            hashed_password=hashed_password,
            **register_data.model_dump(exclude={"password"}),
        )
        try:
            user = await self.db.auth.add(user_to_add)
        except ObjectExistsError as exc:
            raise UserExistsError from exc
        await self.db.commit()
        return user

    async def get_profile(self, username: str) -> UserDTO:
        try:
            return await self.db.auth.get_user_with_passwd(username=username)
        except ObjectNotFoundError as exc:
            raise UserNotFoundError from exc
