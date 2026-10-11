from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends
from fastapi.security import APIKeyCookie

from cloud_storage.auth.entities import Principal
from cloud_storage.auth.exceptions import InvalidTokenError
from cloud_storage.auth.service import AuthService

_security = APIKeyCookie(name="sessionId", auto_error=False)


def get_token(credentials: Annotated[str | None, Depends(_security)]) -> str | None:
    return credentials


SessionToken = Annotated[str | None, Depends(get_token)]


@inject
async def get_current_user(
    token: SessionToken,
    auth_service: FromDishka[AuthService],
) -> Principal:
    if token is None:
        raise InvalidTokenError()

    session = await auth_service.find_session(token)
    if session is None:
        raise InvalidTokenError()

    await auth_service.touch_session(session)

    return await auth_service.get_account(session.account_id)


CurrentUser = Annotated[Principal, Depends(get_current_user)]
