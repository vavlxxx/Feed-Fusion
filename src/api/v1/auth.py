from fastapi import APIRouter, Response

from src.api.v1.dependencies.auth import SubByAccess, SubByRefresh
from src.api.v1.dependencies.db import DBDep
from src.api.v1.responses.auth import (
    AUTH_LOGIN_RESPONSES,
    AUTH_PROFILE_RESPONSES,
    AUTH_REFRESH_RESPONSES,
    AUTH_REGISTER_RESPONSES,
)
from src.schemas.auth import (
    LoginData,
    RegisterData,
    TokenResponseDTO,
    UserDTO,
    UserUpdateDTO,
)
from src.services.auth import AuthService
from src.utils.exceptions import (
    InvalidLoginDataError,
    InvalidLoginDataHTTPError,
    UserExistsError,
    UserExistsHTTPError,
    UserNotFoundError,
    UserNotFoundHTTPError,
)

router = APIRouter(
    prefix="/auth",
    tags=["Аутентификация и авторизация"],
)


@router.post(
    path="/login/",
    responses=AUTH_LOGIN_RESPONSES,
    summary="Войти в аккаунт",
)
async def login(
    db: DBDep,
    login_data: LoginData,
    response: Response,
):
    """
    ## 🔒 Войти в существующий аккаунт
    """
    try:
        token_response: TokenResponseDTO = await AuthService(db).login_user(
            login_data=login_data,
            response=response,
        )
    except InvalidLoginDataError as exc:
        raise InvalidLoginDataHTTPError from exc

    return token_response


@router.post(
    path="/register/",
    responses=AUTH_REGISTER_RESPONSES,
    summary="Зарегистрироваться",
)
async def register(
    db: DBDep,
    register_data: RegisterData,
) -> UserDTO:
    """
    ## 🔒 Зарегистрировать нового пользователя
    """
    try:
        return await AuthService(db).register_user(
            register_data=register_data,
        )
    except UserExistsError as exc:
        raise UserExistsHTTPError from exc


@router.get(
    path="/profile/",
    responses=AUTH_PROFILE_RESPONSES,
    summary="Получить профиль",
)
async def get_profile(
    db: DBDep,
    uid: SubByAccess,
) -> UserDTO:
    """
    ## 🔒 Профиль авторизованного пользователя
    """
    try:
        return await AuthService(db).get_profile(uid=uid)
    except UserNotFoundError as exc:
        raise UserNotFoundHTTPError from exc


@router.put(
    path="/profile/",
    responses=AUTH_PROFILE_RESPONSES,
    summary="Обновить профиль",
)
async def update_profile(
    db: DBDep,
    uid: SubByAccess,
    data: UserUpdateDTO,
) -> UserDTO:
    """
    ## 👤 Обновить профиль пользователя
    """
    profile = await AuthService(db).update_profile(uid=uid, data=data)
    return profile


@router.get(
    path="/refresh/",
    responses=AUTH_REFRESH_RESPONSES,
    summary="Обновить токены",
)
async def refresh(
    db: DBDep,
    uid: SubByRefresh,
    response: Response,
) -> TokenResponseDTO:
    """
    ## 🗝️ Получить новые access и refresh токены
    """
    token_response: TokenResponseDTO = await AuthService(db).update_tokens(
        uid=uid,
        response=response,
    )

    return token_response
