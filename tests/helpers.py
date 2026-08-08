from typing import Any

from httpx import Response


def get_response_error(response: Response) -> Any:
    try:
        body = response.json()
    except ValueError:
        return response.text

    if response.status_code == 422 and isinstance(body, dict):
        return body.get("detail", body)

    if response.status_code > 400:
        return body.get("message", "No error message")

    return body
