from dishka import Provider, Scope, provide

from cloud_storage.auth.ports import PasswordHasher

from .hasher import Argon2PasswordHasher


class Argon2PasswordHasherProvider(Provider):
    @provide(scope=Scope.APP)
    def repository(self) -> PasswordHasher:
        return Argon2PasswordHasher()
