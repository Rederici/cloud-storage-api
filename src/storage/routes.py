from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query
from starlette import status

from src.auth.dependencies import CurrentUser
from src.core.schemas import ErrorResponse
from src.storage.schemas import DirectoryRequest

from .schemas import DirectoryResponse, PathRequest, ResourceResponse, ResourcesResponse
from .service import StorageService
from .types import StoredResource

resource_router = APIRouter(route_class=DishkaRoute)
directory_router = APIRouter(route_class=DishkaRoute)


@resource_router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    },
)
async def get_resource(
    query: Annotated[PathRequest, Query()],
    storage_service: FromDishka[StorageService],
) -> ResourceResponse: ...


@resource_router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Resource deleted"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    },
)
async def delete_resource() -> None: ...


@resource_router.get(
    "/download",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    },
)
async def download_resource(): ...


@resource_router.post(
    "/move",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
        409: {"model": ErrorResponse, "description": "Resource already exists at the destination"},
    },
)
async def move_resource() -> ResourceResponse: ...


@resource_router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def search_resource() -> ResourcesResponse: ...


@resource_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Resource created"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Resource already exists"},
    },
)
async def upload_resource() -> ResourcesResponse: ...


@directory_router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": ResourcesResponse, "description": "Directory found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Directory not found"},
    },
)
async def list_directory(
    user: CurrentUser,
    storage_service: FromDishka[StorageService],
    query: Annotated[DirectoryRequest, Query()],
) -> ResourcesResponse:
    items = await storage_service.list_directory(user.id, query.path)
    return [ResourceResponse.from_domain(item) for item in items]


@directory_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": DirectoryResponse, "description": "Directory created"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Parent directory not found"},
        409: {"model": ErrorResponse, "description": "Directory already exists"},
    },
)
async def create_directory(
    user: CurrentUser,
    storage_service: FromDishka[StorageService],
    query: Annotated[DirectoryRequest, Query()],
) -> DirectoryResponse:
    await storage_service.create_folder(user.id, query.path)
    return DirectoryResponse(path=query.path.parent, name=query.path.name)
