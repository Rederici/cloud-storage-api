from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import Depends

from cloud_storage.auth.entities import Account
from cloud_storage.auth.exceptions import InvalidTokenError
from cloud_storage.auth.service import AuthService
from cloud_storage.security import security


def get_token(credentials: Annotated[str, Depends(security)]) -> str | None:
    return credentials


SessionToken = Annotated[str, Depends(get_token)]


@inject
async def get_current_user(
    token: SessionToken,
    auth_service: FromDishka[AuthService],
) -> Account:
    session = await auth_service.find_session(token)
    if session is None:
        raise InvalidTokenError()

    await auth_service.touch_session(token)

    return await auth_service.get_account(session.account_id)


CurrentUser = Annotated[Account, Depends(get_current_user)]
