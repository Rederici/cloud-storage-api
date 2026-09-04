from typing import Any


class AppError(Exception):
    message: str = "Unknown error"

    def __init__(self, message: str | None = None, **kwargs: Any):
        self.message = (message or self.message).format(**kwargs)
        super().__init__(self.message)
