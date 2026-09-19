from dishka import Provider, Scope, provide

from .ports import StorageRepository
from .service import StorageService


class StorageProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def service(self, storage_repo: StorageRepository) -> StorageService:
        return StorageService(storage_repo=storage_repo)
