from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
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


async def base_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=exc.detail).model_dump(mode="json"),
    )


async def validation_error_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = []

    for error in exc.errors():
        location = error["loc"]

        if location and location[0] in {"body", "query", "path", "header"}:
            location = location[1:]

        field = ".".join(str(part) for part in location)

        message = error["msg"]

        errors.append(f"{field}: {message}")

    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            message="; ".join(errors),
        ).model_dump(mode="json"),
    )


async def error_handler(_: Request, exc: AppError) -> JSONResponse:
    status_code = get_status_code(exc)
    message = exc.message or "Internal Server Error"

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(message=message).model_dump(mode="json"),
    )
