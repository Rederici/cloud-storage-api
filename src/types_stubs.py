from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client
    from types_aiobotocore_s3.type_defs import (
        CommonPrefixTypeDef,
        HeadObjectOutputTypeDef,
        ListObjectsV2RequestPaginateTypeDef,
        ObjectTypeDef,
    )
else:
    S3Client = object
    CommonPrefixTypeDef = object
    HeadObjectOutputTypeDef = object
    ListObjectsV2RequestPaginateTypeDef = object
    ObjectTypeDef = object

__all__ = [
    "CommonPrefixTypeDef",
    "HeadObjectOutputTypeDef",
    "ListObjectsV2RequestPaginateTypeDef",
    "ObjectTypeDef",
    "S3Client",
]
