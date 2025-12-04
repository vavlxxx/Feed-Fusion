from typing import Any, Dict

from fastapi import status

from src.schemas.auth import TokenResponseDTO, UserDTO, UserRole
from src.utils.exceptions import (
    ExpiredSignatureHTTPError,
    InvalidLoginDataHTTPError,
    InvalidTokenTypeHTTPError,
    MissingSubjectHTTPError,
    MissingTokenHTTPError,
    UserExistsHTTPError,
    UserNotFoundHTTPError,
    WithdrawnTokenHTTPError,
)

AUTH_REFRESH_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    status.HTTP_200_OK: {
        "description": "Токены успешно обновлены",
        "model": TokenResponseDTO,
        "example": TokenResponseDTO(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30",
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30",
        ),
    },
    status.HTTP_403_FORBIDDEN: {
        "description": "Отозванный или просроченный refresh токен",
        "content": {
            "application/json": {"example": {"detail": WithdrawnTokenHTTPError.detail}}
        },
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "Некорректные данные",
        "content": {
            "application/json": {
                "examples": {
                    "InvalidTokenType": {
                        "description": "Неверный тип токена",
                        "value": {
                            "detail": InvalidTokenTypeHTTPError.detail,
                        },
                    },
                    "MissingSubject": {
                        "description": "В токене отсутствует поле 'sub'",
                        "value": {
                            "detail": MissingSubjectHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        "summary": "Не аутентифицирован",
        "content": {
            "application/json": {
                "examples": {
                    "MissingToken": {
                        "description": "Отсутствует access токен",
                        "value": {
                            "detail": MissingTokenHTTPError.detail,
                        },
                    },
                    "ExpiredSignature": {
                        "description": "Просроченная подпись токена",
                        "value": {
                            "detail": ExpiredSignatureHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
}


AUTH_LOGIN_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    status.HTTP_200_OK: {
        "description": "Успешная авторизация пользователя",
        "model": TokenResponseDTO,
        "example": TokenResponseDTO(
            access_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30",
            refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.KMUFsIDTnFmyG3nMiGM6H9FNFUROf3wh7SmqJp-QV30",
        ),
    },
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Неверные данные для входа",
        "content": {
            "application/json": {
                "example": {"detail": InvalidLoginDataHTTPError.detail}
            }
        },
    },
}


AUTH_REGISTER_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    status.HTTP_200_OK: {
        "description": "Успешная регистрация пользователя",
        "model": UserDTO,
        "example": UserDTO(
            id=1,
            username="test",
            role=UserRole.CUSTOMER,
            telegram_id=None,
            first_name=None,
            last_name=None,
        ),
    },
    status.HTTP_409_CONFLICT: {
        "description": "Пользователь с таким username уже зарегистрирован",
        "content": {
            "application/json": {"example": {"detail": UserExistsHTTPError.detail}}
        },
    },
}


AUTH_PROFILE_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    status.HTTP_200_OK: {
        "description": "Профиль пользователя",
        "model": UserDTO,
        "example": UserDTO(
            id=1,
            username="test",
            role=UserRole.CUSTOMER,
            telegram_id=None,
            first_name=None,
            last_name=None,
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "description": "Пользователь не найден",
        "content": {
            "application/json": {"example": {"detail": UserNotFoundHTTPError.detail}}
        },
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "description": "Некорректные данные",
        "content": {
            "application/json": {
                "examples": {
                    "InvalidTokenType": {
                        "description": "Неверный тип токена",
                        "value": {
                            "detail": InvalidTokenTypeHTTPError.detail,
                        },
                    },
                    "MissingSubject": {
                        "description": "В токене отсутствует поле 'sub'",
                        "value": {
                            "detail": MissingSubjectHTTPError.detail,
                        },
                    },
                }
            },
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Не аутентифицирован",
        "content": {
            "application/json": {
                "examples": {
                    "MissingToken": {
                        "summary": "MissingToken",
                        "value": {
                            "detail": MissingTokenHTTPError.detail,
                        },
                    },
                    "ExpiredSignature": {
                        "description": "Просроченная подпись токена",
                        "value": {
                            "detail": ExpiredSignatureHTTPError.detail,
                        },
                    },
                },
            },
        },
    },
}
