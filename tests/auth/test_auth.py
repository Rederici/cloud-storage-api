import pytest
from httpx import AsyncClient

from cloud_storage.auth.http.schemas import CredentialsRequest
from cloud_storage.config import Config


async def test_register_success(client: AsyncClient, user: CredentialsRequest, config: Config):
    response = await client.post("/api/v1/auth/sign-up", json=user.model_dump())
    assert response.status_code == 201
    assert config.app.session.cookie_name in response.cookies


@pytest.mark.parametrize(
    "invalid_payload",
    [
        {"username": "inv@lid-us3rn4me", "password": "Valid_Password123"},
        {"username": "sml", "password": "Valid_Password123"},
        {"username": "VeryVeryVeryVeryVeryLongUsername", "password": "Valid_Password123"},
        {"username": "valid_username", "password": "Ez@1pw"},
        {"username": "valid_username", "password": "Long@1pwd" * 10},
        {"username": "valid_username", "password": "nouppercase123!"},
        {"username": "valid_username", "password": "NOLOWERCASE123!"},
        {"username": "valid_username", "password": "NoDigitsHere!!"},
        {"username": "valid_username", "password": "NoSpecial12345"},
        {"username": "valid_username"},
        {"password": "Valid_Password123"},
        {},
    ],
    ids=[
        "username-with-forbidden-characters",
        "username-too-short",
        "username-too-long",
        "password-too-short",
        "password-too-long",
        "password-without-uppercase",
        "password-without-lowercase",
        "password-without-digit",
        "password-without-special-character",
        "missing-password",
        "missing-username",
        "missing-username-and-password",
    ],
)
async def test_register_invalid_payload_returns_400(client: AsyncClient, invalid_payload: dict):
    response = await client.post("/api/v1/auth/sign-up", json=invalid_payload)
    assert response.status_code == 400


async def test_register_duplicate_email_returns_409(client: AsyncClient, registered_user: CredentialsRequest):
    response = await client.post("/api/v1/auth/sign-up", json=registered_user.model_dump())
    assert response.status_code == 409, response.json()["message"]


async def test_login_success(client: AsyncClient, registered_user: CredentialsRequest, config: Config):
    response = await client.post("/api/v1/auth/sign-in", json=registered_user.model_dump())
    assert response.status_code == 200
    assert config.app.session.cookie_name in response.cookies


async def test_invalid_username_login_returns_401(client: AsyncClient, registered_user: CredentialsRequest):
    registered_user.username += "A"
    response = await client.post("/api/v1/auth/sign-in", json=registered_user.model_dump())
    assert response.status_code == 401, response.json()["message"]


async def test_invalid_password_login_returns_401(client: AsyncClient, registered_user: CredentialsRequest):
    registered_user.password += "A"
    response = await client.post("/api/v1/auth/sign-in", json=registered_user.model_dump())
    assert response.status_code == 401


async def test_registered_logout_success(client: AsyncClient, registered_user: CredentialsRequest):
    response = await client.post("/api/v1/auth/sign-out")
    assert response.status_code == 204


async def test_unregistered_logout_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/sign-out")
    assert response.status_code == 204


async def test_get_user_info(client: AsyncClient, registered_user: CredentialsRequest):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200, response.json()["message"]
    assert response.json().get("username") == registered_user.username


async def test_get_user_info_with_empty_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_user_info_with_invalid_token_returns_401(
    client: AsyncClient,
    registered_user: CredentialsRequest,
    config: Config,
):
    client.cookies.set(
        config.app.session.cookie_name,
        str(client.cookies.get(config.app.session.cookie_name)) + "A",
    )

    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
