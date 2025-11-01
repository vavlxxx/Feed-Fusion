from typing import Any, Dict

from src.schemas.auth import TokenResponseDTO, UserDTO
from src.utils.exceptions import (
    ExpiredSignatureHTTPError,
    InvalidLoginDataHTTPError,
    InvalidTokenTypeHTTPError,
    MissingSubjectHTTPError,
    MissingTokenHTTPError,
    UserNotFoundHTTPError,
    WithdrawnTokenHTTPError,
)

AUTH_REFRESH_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    "200": {"model": TokenResponseDTO},
    "403": {
        "summary": "Список возможных ошибок",
        "content": {
            "application/json": {
                "examples": {
                    "WithdrawnToken": {
                        "summary": "WithdrawnToken",
                        "value": {
                            "detail": WithdrawnTokenHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
    "422": {
        "summary": "Список возможных ошибок",
        "content": {
            "application/json": {
                "examples": {
                    "InvalidTokenType": {
                        "summary": "InvalidTokenType",
                        "value": {
                            "detail": InvalidTokenTypeHTTPError.detail,
                        },
                    },
                    "MissingSubject": {
                        "summary": "MissingSubject",
                        "value": {
                            "detail": MissingSubjectHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
    "401": {
        "summary": "Список возможных ошибок",
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
                        "summary": "ExpiredSignature",
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
    "200": {"model": TokenResponseDTO},
    "401": {
        "summary": "Список возможных ошибок",
        "content": {
            "application/json": {
                "examples": {
                    "InvalidLoginData": {
                        "summary": "InvalidLoginData",
                        "value": {
                            "detail": InvalidLoginDataHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
}


AUTH_REGISTER_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    "200": {"model": UserDTO},
}


AUTH_PROFILE_RESPONSES: Dict[int | str, Dict[str, Any]] | None = {
    "200": {"model": UserDTO},
    "404": {
        "summary": "Список возможных ошибок",
        "content": {
            "application/json": {
                "examples": {
                    "UserNotFound": {
                        "summary": "UserNotFound",
                        "value": {
                            "detail": UserNotFoundHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
    "422": {
        "summary": "Список возможных ошибок",
        "content": {
            "application/json": {
                "examples": {
                    "InvalidTokenType": {
                        "summary": "InvalidTokenType",
                        "value": {
                            "detail": InvalidTokenTypeHTTPError.detail,
                        },
                    },
                    "MissingSubject": {
                        "summary": "MissingSubject",
                        "value": {
                            "detail": MissingSubjectHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
    "401": {
        "summary": "Список возможных ошибок",
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
                        "summary": "ExpiredSignature",
                        "value": {
                            "detail": ExpiredSignatureHTTPError.detail,
                        },
                    },
                }
            }
        },
    },
}
