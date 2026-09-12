from typing import Annotated

from dishka import FromDishka as Inject
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from src.api.http.schemas import ErrorResponse
from src.auth.dependencies import CurrentUser

from .dependencies import VerifiedFiles
from .schemas import (
    AnyPath,
    DirectoryResponse,
    DirPath,
    ResourceResponse,
)
from .service import StorageService
from .types import ResourceType

ResourceRouter = APIRouter(route_class=DishkaRoute, prefix="/resources", tags=["Resources"])
DirectoryRouter = APIRouter(route_class=DishkaRoute, prefix="/directory", tags=["Directory"])


@ResourceRouter.get(
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
    path: AnyPath = Query(default="/"),
) -> ResourceResponse:
    item = await storage_service.get(path, user_id=user.id)
    return ResourceResponse.from_domain(item)


@ResourceRouter.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Resource deleted"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    },
)
async def delete_resource(
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    path: Annotated[AnyPath, Query()],
) -> None:
    await storage_service.delete(path, user_id=user.id)


@ResourceRouter.get(
    "/download",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
    },
)
async def download_resource(
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    path: Annotated[AnyPath, Query()],
):
    result = await storage_service.download(path, user_id=user.id)
    return StreamingResponse(
        result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{result.filename}"',
        },
    )


@ResourceRouter.post(
    "/move",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource not found"},
        409: {"model": ErrorResponse, "description": "Resource already exists at the destination"},
    },
)
async def move_resource(
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    source: Annotated[AnyPath, Query(alias="from")],
    dest: Annotated[AnyPath, Query(alias="to")],
) -> ResourceResponse:
    return ResourceResponse.from_domain(
        await storage_service.move(source, dest, user_id=user.id),
    )


@ResourceRouter.get(
    "/search",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Resource found"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def search_resource(
    user: CurrentUser,
    storage_service: Inject[StorageService],
    *,
    query: str = Query(min_length=1, max_length=128),
) -> list[ResourceResponse]:
    items = await storage_service.search(query, user_id=user.id)
    return [ResourceResponse.from_domain(i) for i in items]


@ResourceRouter.post(
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
    path: Annotated[DirPath, Query()],
    files: VerifiedFiles,
) -> list[ResourceResponse]:
    await storage_service.upload_files(files, path=path, user_id=user.id)

    items = []
    for file in files:
        file_path = path / file.filename
        items.append(
            ResourceResponse(
                path=str(file_path.parent),
                name=file_path.name,
                size=file.size or 0,
                type=ResourceType.FILE,
            )
        )
    return items


@DirectoryRouter.get(
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
    path: DirPath = Query(default=""),
) -> list[ResourceResponse]:
    items = await storage_service.list_directory(path, user_id=user.id)
    return [ResourceResponse.from_domain(item) for item in items]


@DirectoryRouter.post(
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
    path: Annotated[DirPath, Query()],
) -> DirectoryResponse:
    await storage_service.create_folder(path, user_id=user.id)
    return DirectoryResponse(path=path.parent, name=path.name)
