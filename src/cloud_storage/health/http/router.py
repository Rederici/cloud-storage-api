from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter

from cloud_storage.config import Config

from .schemas import HealthResponse

router = APIRouter(route_class=DishkaRoute, prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
async def health(config: FromDishka[Config]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=config.project.display_name,
        version=config.project.version,
    )
