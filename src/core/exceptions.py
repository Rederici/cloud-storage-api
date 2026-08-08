from typing import Any

from starlette import status

from src.core.schemas import ErrorResponse


class AppError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Unknown error"

    def __init__(
        self,
        message: str | None = None,
        *,
        status_code: int | None = None,
        **params: Any,
    ) -> None:
        self.status_code = status_code or self.__class__.status_code
        template = message or self.__class__.message

        try:
            self.message = template.format(**params)
        except KeyError as e:
            missing_param = e.args[0]
            raise TypeError(f"Missing error message parameter: {missing_param!r}") from e

        super().__init__(self.message)

    def to_model(self) -> ErrorResponse:
        return ErrorResponse(message=self.message)
