from botocore.exceptions import ClientError

from cloud_storage.types_stubs import S3Client


class StorageInitializer:
    def __init__(self, s3_client: S3Client, bucket_name: str):
        self._s3 = s3_client
        self._bucket_name = bucket_name

    async def init_bucket(self) -> None:
        try:
            await self._s3.create_bucket(Bucket=self._bucket_name)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") not in (
                "BucketAlreadyOwnedByYou",
                "BucketAlreadyExists",
            ):
                raise
