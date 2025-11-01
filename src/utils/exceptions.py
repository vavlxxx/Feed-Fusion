from fastapi import HTTPException, status


class ApplicationError(Exception):
    detail = "Something went wrong"

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(self.detail)


class MissingTablesError(ApplicationError):
    detail = "Missing tables"

    def __init__(self, detail: set | None = None):
        if detail is not None and isinstance(detail, set):
            self.detail = f"{self.detail}: %s" % ", ".join(map(repr, detail))
        super().__init__(self.detail)


class ObjectNotFoundError(ApplicationError):
    detail = "Object not found"


class ChannelNotFoundError(ObjectNotFoundError):
    pass


class ObjectExistsError(ApplicationError):
    detail = "Object already exists"


class ChannelExistsError(ObjectExistsError):
    pass


class ValueOutOfRangeError(ApplicationError):
    detail = "Value out of integer range"


class InvalidLoginDataError(ApplicationError):
    detail = "Invalid login data, wrong password or username"


class UserExistsError(ObjectExistsError):
    detail = "User already exists"


class UserNotFoundError(ApplicationError):
    detail = "User not found"


class ApplicationHTTPError(HTTPException):
    detail = "Something went wrong"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(detail=self.detail, status_code=self.status_code)


class ValueOutOfRangeHTTPError(ApplicationHTTPError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detail = "Value out of valid range"


class ChannelNotFoundHTTPError(ApplicationHTTPError):
    detail = "Channel not found"
    status_code = status.HTTP_404_NOT_FOUND


class ChannelExistsErrorHTTPError(ApplicationHTTPError):
    detail = "Channel already exists"
    status_code = status.HTTP_409_CONFLICT


class ExpiredSignatureHTTPError(ApplicationHTTPError):
    detail = "Token has expired, try to login again"
    status_code = status.HTTP_401_UNAUTHORIZED


class InvalidTokenTypeHTTPError(ApplicationHTTPError):
    detail = "Invalid token type, expected {}, got {}"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, *args, expected_type, actual_type, **kwargs):
        self.detail = self.detail.format(expected_type, actual_type)
        super().__init__(*args, detail=self.detail, **kwargs)


class WithdrawnTokenHTTPError(ApplicationHTTPError):
    detail = "Withdrawn refresh token, try to login again"
    status_code = status.HTTP_403_FORBIDDEN


class MissingSubjectHTTPError(ApplicationHTTPError):
    detail = "Missing token subject field"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class MissingTokenHTTPError(ApplicationHTTPError):
    detail = "Missing token"
    status_code = status.HTTP_401_UNAUTHORIZED


class UserNotFoundHTTPError(ApplicationHTTPError):
    detail = "User not found"
    status_code = status.HTTP_404_NOT_FOUND


class UserExistsHTTPError(ApplicationHTTPError):
    detail = "User already exists"
    status_code = status.HTTP_409_CONFLICT


class InvalidLoginDataHTTPError(ApplicationHTTPError):
    detail = "Invalid login data, wrong password or username"
    status_code = status.HTTP_401_UNAUTHORIZED
