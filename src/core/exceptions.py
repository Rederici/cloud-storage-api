from starlette import status

from src.core.schemas import ErrorResponse


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Unknown error"

    def __init__(self, status_code: int | None = None, detail: str | None = None) -> None:
        self.status_code = status_code or self.__class__.status_code
        self.message = detail or self.__class__.message
        super().__init__(self.message)

    def to_model(self) -> ErrorResponse:
        return ErrorResponse(message=self.message)
