from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends, File, UploadFile
from pydantic import AfterValidator

from cloud_storage.config import Config
from cloud_storage.storage.exceptions import ContentSizeExceeded, TooManyFiles
from cloud_storage.storage.http.schemas import (
    ValidatedUploadFile,
    ValidatedUploadFiles,
    validate_unique_filenames,
)


@inject
def verify_files_size(
    config: FromDishka[Config],
    files: Annotated[
        list[ValidatedUploadFile],
        File(),
        AfterValidator(validate_unique_filenames),
    ],
) -> ValidatedUploadFiles:
    if len(files) > config.app.files.max_count:
        raise TooManyFiles()

    total_size = 0
    for file in files:
        if file.size is None:
            raise ContentSizeExceeded()

        total_size += file.size

        if total_size > config.app.files.max_total_size:
            raise ContentSizeExceeded()

    return files


VerifiedFiles = Annotated[list[UploadFile], Depends(verify_files_size)]
