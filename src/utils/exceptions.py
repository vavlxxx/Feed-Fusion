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
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Channel not found"


class ChannelExistsErrorHTTPError(ApplicationHTTPError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Channel already exists"
