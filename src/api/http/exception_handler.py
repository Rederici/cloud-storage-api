from starlette.requests import Request
from starlette.responses import JSONResponse

from src.exceptions import AppError

from .exceptions import mapping
from .schemas import ErrorResponse


def get_status_code(exc: AppError) -> int:
    for error_type in type(exc).__mro__:
        if status_code := mapping.get(error_type):
            return status_code

    return 500


async def error_handler(_: Request, exc: AppError) -> JSONResponse:
    status_code = get_status_code(exc)
    message = exc.message or "Internal Server Error"

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(message=message).model_dump(mode="json"),
    )
