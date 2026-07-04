from starlette.requests import Request
from starlette.responses import JSONResponse

from src.core import AppError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_model().model_dump()
    )
