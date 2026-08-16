from src.bootstrap import create_app, create_container
from src.core.config import Config
from src.core.dependencies import InfrastructureProvider

config = Config()
app = create_app(
    config=config,
    container=create_container(InfrastructureProvider(), context={Config: config}),
)
