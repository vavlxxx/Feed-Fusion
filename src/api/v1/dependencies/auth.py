from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError

from src.api.v1.dependencies.db import DBDep
from src.schemas.auth import TokenType
from src.services.auth import AuthService
from src.utils.exceptions import (
    ExpiredSignatureHTTPError,
    InvalidTokenTypeHTTPError,
    MissingSubjectHTTPError,
    MissingTokenHTTPError,
    ObjectNotFoundError,
    WithdrawnTokenHTTPError,
    AdminAllowedHTTPError,
)

_bearer = HTTPBearer()
BearerCredentials = Annotated[HTTPAuthorizationCredentials, Depends(_bearer)]


def _get_access_token(creds: BearerCredentials):
    return creds.credentials


def _get_refresh_token(request: Request):
    token = request.cookies.get("refresh_token")
    if not token:
        raise MissingTokenHTTPError
    return token


def _decode_token(token: str):
    try:
        return AuthService().decode_token(token)
    except ExpiredSignatureError as exc:
        raise ExpiredSignatureHTTPError from exc


def _validate_token_type(payload: dict, expected_type: TokenType):
    token_type = payload.get("type")
    if not token_type or token_type != expected_type.value:
        raise InvalidTokenTypeHTTPError(
            expected_type=expected_type.value,
            actual_type=token_type,
        )


def _extract_token_subject(payload: dict) -> str:
    sub = payload.get("sub")
    if not sub:
        raise MissingSubjectHTTPError
    return sub


def resolve_token_by_type(token_type: TokenType):
    if token_type == TokenType.ACCESS:

        def get_sub_from_access(creds: BearerCredentials):
            payload = _decode_token(_get_access_token(creds))
            _validate_token_type(payload, token_type)
            return int(_extract_token_subject(payload))

        return get_sub_from_access

    elif token_type == TokenType.REFRESH:

        async def get_sub_from_refresh(request: Request, db: DBDep):
            payload = _decode_token(_get_refresh_token(request))
            _validate_token_type(payload, token_type)
            uid = int(_extract_token_subject(payload))
            try:
                await db.tokens.get_one(owner_id=uid, type=token_type)
            except ObjectNotFoundError as exc:
                raise WithdrawnTokenHTTPError from exc
            return uid

        return get_sub_from_refresh


def inspect_user_role(access_token: str = Depends(_get_access_token)) -> bool:
    if access_token:
        payload = {}
        try:
            payload = _decode_token(access_token)
            _validate_token_type(payload, TokenType.ACCESS)
        except Exception as _:
            ...
        return payload.get("is_admin", False)
    return False


def only_admins(is_admin: bool = Depends(inspect_user_role)):
    if not is_admin:
        raise AdminAllowedHTTPError


AdminAllowedDep = Annotated[None, Depends(only_admins)]
IsAdminDep = Annotated[bool, Depends(inspect_user_role)]
SubByAccess = Annotated[str, Depends(resolve_token_by_type(TokenType.ACCESS))]
SubByRefresh = Annotated[int, Depends(resolve_token_by_type(TokenType.REFRESH))]
