from typing import Annotated

from dishka import FromDishka as Inject
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query, UploadFile, status, File
from src.auth.dependencies import CurrentUser
from src.core.schemas import ErrorResponse
from .dependencies import VerifiedFiles

from .schemas import (
    AnyPath,
    DirectoryResponse,
    DirPath,
    FilePath,
    ResourceResponse,
)
from .service import StorageService
from .types import ResourceType

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
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    path: AnyPath,
) -> ResourceResponse:
    item = await storage_service.get(path, user_id=user.id)
    return ResourceResponse.from_domain(item)


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
        201: {"model": list[ResourceResponse], "description": "Resource created"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Resource already exists"},
    },
)
async def upload_resource(
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    path: DirPath,
    files: VerifiedFiles
) -> list[ResourceResponse]:
    await storage_service.upload_files(files, path=path, user_id=user.id)

    items = []
    for file in files:
        file_path = path / file.filename
        items.append(
            ResourceResponse(
                path=str(file_path.parent),
                name=file_path.name,
                size=file.size | 0,
                type=ResourceType.FILE,
            )
        )
    return items


@directory_router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": list[ResourceResponse], "description": "Directory found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Directory not found"},
    },
)
async def list_directory(
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    path: DirPath,
) -> list[ResourceResponse]:
    items = await storage_service.list_directory(path, user_id=user.id)
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
    storage_service: Inject[StorageService],
    *,
    path: DirPath,
) -> DirectoryResponse:
    await storage_service.create_folder(path, user_id=user.id)
    return DirectoryResponse(path=path.parent, name=path.name)
