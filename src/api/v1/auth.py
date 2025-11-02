from fastapi import APIRouter, Response

from src.api.v1.dependencies.auth import IsAdminDep, SubByRefresh, SubByAccess
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
    tags=["Authentication and Authorization"],
)


@router.post(
    path="/login/",
    responses=AUTH_LOGIN_RESPONSES,
)
async def login(
    db: DBDep,
    login_data: LoginData,
    response: Response,
):
    """
    ## 🔒 Login to existing user account
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
)
async def register(
    db: DBDep,
    register_data: RegisterData,
):
    """
    ## 🔒 Register new user

    Only username and password are required
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
)
async def get_profile(
    db: DBDep,
    uid: SubByAccess,
) -> UserDTO:
    """
    ## 🔒 Authorized user profile

    Example of data which can be stored in User model of database
    """
    try:
        return await AuthService(db).get_profile(uid=uid)
    except UserNotFoundError as exc:
        raise UserNotFoundHTTPError from exc


@router.put(
    path="/profile/",
)
async def update_profile(
    db: DBDep,
    uid: SubByAccess,
    data: UserUpdateDTO,
) -> UserDTO:
    """
    ## 👤 Update profile

    Provide at least one non-empty field to update your plofile data
    """
    profile = await AuthService(db).update_profile(uid=uid, data=data)
    return profile


@router.get(
    path="/refresh/",
    responses=AUTH_REFRESH_RESPONSES,
)
async def refresh(
    db: DBDep,
    uid: SubByRefresh,
    response: Response,
) -> TokenResponseDTO:
    """
    ## 🗝️ Get new access and refresh tokens

    Authorized user can get new access and refresh tokens by restoring refresh token from **http only** cookie `refresh_token`
    """
    token_response: TokenResponseDTO = await AuthService(db).update_tokens(
        uid=uid,
        response=response,
    )

    return token_response
