from dishka import Provider, Scope, provide

from .models import Config


class ConfigProvider(Provider):
    @provide(scope=Scope.APP)
    def config(self) -> Config:
        return Config()
