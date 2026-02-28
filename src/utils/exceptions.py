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
            self.detail = f"{self.detail}: %s" % ", ".join(
                map(repr, detail)
            )
        super().__init__(self.detail)


class AlreadyAssignedCategoryError(ApplicationError):
    detail = "Provided already assigned category"


class ObjectNotFoundError(ApplicationError):
    detail = "Object not found"


class UploadNotFoundError(ObjectNotFoundError):
    detail = "Upload not found"


class NewsNotFoundError(ObjectNotFoundError):
    detail = "News not found"


class ChannelNotFoundError(ObjectNotFoundError):
    detail = "Channel not found"


class ObjectExistsError(ApplicationError):
    detail = "Object already exists"


class DenormalizedNewsAlreadyExistsError(ObjectExistsError):
    detail = "Denormalized news already exists"


class ChannelExistsError(ObjectExistsError):
    detail = "Channel already exists"


class SubExistsError(ObjectExistsError):
    detail = "Subscription already exists"


class EmptyChannelError(ObjectNotFoundError):
    detail = "Channel is empty"


class MisingTelegramError(ApplicationError):
    detail = "Missing telegram id"


class ValueOutOfRangeError(ApplicationError):
    detail = "Value out of integer range"


class InvalidLoginDataError(ApplicationError):
    detail = "Invalid login data, wrong password or username"


class UserExistsError(ObjectExistsError):
    detail = "User already exists"


class UserNotFoundError(ObjectNotFoundError):
    detail = "User not found"


class SubNotFoundError(ObjectNotFoundError):
    detail = "Subscription not found"


class TrainingNotFoundError(ObjectNotFoundError):
    detail = "Training not found"


class CSVDecodeError(ApplicationError):
    detail = "Cannot decode provided CSV file"


class BrokerUnavailableError(ApplicationError):
    detail = "Message broker is unavailable"


class ModelAlreadyTrainingError(ObjectExistsError):
    detail = "Model is currently training"


class MissingCSVHeadersError(ApplicationError):
    detail = "Missing CSV headers"

    def __init__(self, detail: set | None = None):
        if detail and isinstance(detail, set):
            self.detail = f"{self.detail}: %s" % ",".join(
                map(repr, detail)
            )
        super().__init__(self.detail)


class MissingDatasetClassesError(MissingCSVHeadersError):
    detail = "Missing dataset classes"


class ApplicationHTTPError(HTTPException):
    detail = "Something went wrong"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: str | None = None):
        if detail is not None:
            self.detail = detail
        super().__init__(
            detail=self.detail, status_code=self.status_code
        )


class ValueOutOfRangeHTTPError(ApplicationHTTPError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detail = "Value out of valid range"


class AdminAllowedHTTPError(ApplicationHTTPError):
    detail = "Only admins allowed"
    status_code = status.HTTP_403_FORBIDDEN


class AlreadyAssignedCategoryHTTPError(ApplicationHTTPError):
    detail = "Provided already assigned category"
    status_code = status.HTTP_400_BAD_REQUEST


class DenormalizedNewsAlreadyExistsHTTPError(ApplicationHTTPError):
    detail = "Denormalized news already exists"
    status_code = status.HTTP_409_CONFLICT


class SubNotFoundHTTPError(ApplicationHTTPError):
    detail = "Subscription not found"
    status_code = status.HTTP_404_NOT_FOUND


class EmptyChannelHTTPError(ApplicationHTTPError):
    detail = "Channel is empty"
    status_code = status.HTTP_404_NOT_FOUND


class MisingTelegramErrorHTTPError(ApplicationHTTPError):
    detail = "Missing telegram id"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class NewsNotFoundHTTPError(ApplicationHTTPError):
    detail = "News not found"
    status_code = status.HTTP_404_NOT_FOUND


class ChannelNotFoundHTTPError(ApplicationHTTPError):
    detail = "Channel not found"
    status_code = status.HTTP_404_NOT_FOUND


class ChannelExistsErrorHTTPError(ApplicationHTTPError):
    detail = "Channel already exists"
    status_code = status.HTTP_409_CONFLICT


class SubExistsErrorHTTPError(ApplicationHTTPError):
    detail = "Subscription already exists"
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


class UploadNotFoundHTTPError(ApplicationHTTPError):
    detail = "Upload not found"
    status_code = status.HTTP_404_NOT_FOUND


class UserExistsHTTPError(ApplicationHTTPError):
    detail = "User already exists"
    status_code = status.HTTP_409_CONFLICT


class InvalidLoginDataHTTPError(ApplicationHTTPError):
    detail = "Invalid login data, wrong password or username"
    status_code = status.HTTP_401_UNAUTHORIZED


class CSVDecodeHTTPError(ApplicationHTTPError):
    detail = "Cannot decode provided CSV file"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class MissingCSVHeadersHTTPError(ApplicationHTTPError):
    detail = "Missing CSV headers"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class BrokerUnavailableHTTPError(ApplicationHTTPError):
    detail = "Message broker is unavailable"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class ModelAlreadyTrainingHTTPError(ApplicationHTTPError):
    detail = "Model is currently training"
    status_code = status.HTTP_409_CONFLICT


class TrainingNotFoundHTTPError(ApplicationHTTPError):
    detail = "Training not found"
    status_code = status.HTTP_404_NOT_FOUND
