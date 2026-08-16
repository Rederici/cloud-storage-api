import pytest

from src.storage.types import ResourcePath, UserSpacePath


@pytest.mark.parametrize(
    "value",
    [
        "/",
        "/documents/",
        "/documents/report.pdf",
        "/a/b/c/",
        "/a/b/c/file.txt",
    ],
)
def test_resource_path_accepts_valid_paths(
    value: str,
) -> None:
    assert str(ResourcePath(value)) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "documents/",
        "documents/file.txt",
        "//documents/",
        "/documents//reports/",
        r"\documents\file.txt",
        "/documents/./file.txt",
        "/documents/../file.txt",
    ],
)
def test_resource_path_rejects_invalid_paths(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        ResourcePath(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        42,
        [],
    ],
)
def test_resource_path_rejects_non_string_values(
    value: object,
) -> None:
    with pytest.raises(TypeError):
        ResourcePath(value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "is_directory"),
    [
        ("/", True),
        ("/documents/", True),
        ("/documents/report.pdf", False),
        ("/report", False),
    ],
)
def test_resource_path_detects_resource_type(
    value: str,
    is_directory: bool,
) -> None:
    path = ResourcePath(value)

    assert path.is_directory is is_directory
    assert path.is_file is not is_directory


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/", ""),
        ("/documents/", "documents"),
        ("/documents/report.pdf", "report.pdf"),
        ("/a/b/c/", "c"),
    ],
)
def test_resource_path_returns_name(
    value: str,
    expected: str,
) -> None:
    assert ResourcePath(value).name == expected


@pytest.mark.parametrize(
    ("value", "expected_parent"),
    [
        ("/", "/"),
        ("/documents/", "/"),
        ("/report.pdf", "/"),
        ("/documents/report.pdf", "/documents/"),
        ("/a/b/c/", "/a/b/"),
    ],
)
def test_resource_path_returns_parent(
    value: str,
    expected_parent: str,
) -> None:
    assert str(ResourcePath(value).parent) == expected_parent


@pytest.mark.parametrize(
    ("base", "child", "expected"),
    [
        ("/", "documents/", "/documents/"),
        ("/", "file.txt", "/file.txt"),
        ("/documents/", "reports/", "/documents/reports/"),
        ("/documents/", "report.pdf", "/documents/report.pdf"),
    ],
)
def test_resource_path_joins_child(
    base: str,
    child: str,
    expected: str,
) -> None:
    assert ResourcePath(base) / child == ResourcePath(expected)


def test_resource_path_joins_another_resource_path() -> None:
    result = ResourcePath("/documents/") / ResourcePath("/reports/2026/")
    assert result == ResourcePath("/documents/reports/2026/")


def test_file_cannot_have_children() -> None:
    with pytest.raises(ValueError, match="Children can only be added"):
        _ = ResourcePath("/documents/report.pdf") / "nested.txt"


def test_equal_resource_paths_are_equal() -> None:
    first = ResourcePath("/documents/")
    second = ResourcePath("/documents/")

    assert first == second
    assert hash(first) == hash(second)


def test_resource_path_can_be_used_in_set() -> None:
    paths = {
        ResourcePath("/documents/"),
        ResourcePath("/documents/"),
    }

    assert len(paths) == 1


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("/", "user-42-files/"),
        ("/documents/", "user-42-files/documents/"),
        ("/documents/report.pdf", "user-42-files/documents/report.pdf"),
    ],
)
def test_user_space_path_returns_storage_key(
    value: str,
    expected: str,
) -> None:
    path = UserSpacePath(value=value, user_id=42)
    assert path.storage_key == expected


def test_user_space_path_returns_public_path() -> None:
    path = UserSpacePath(value="/documents/report.pdf", user_id=42)
    assert path.public_path == ResourcePath("/documents/report.pdf")


def test_user_space_root() -> None:
    root = UserSpacePath(value="/", user_id=42)

    assert root.is_root
    assert root.is_directory
    assert root.storage_key == "user-42-files/"


def test_user_space_parent_preserves_user_id() -> None:
    parent = UserSpacePath(value="/documents/report.pdf", user_id=42).parent

    assert isinstance(parent, UserSpacePath)
    assert parent.user_id == 42
    assert parent.value == "/documents/"
    assert parent.storage_key == "user-42-files/documents/"


def test_user_space_join_preserves_user_id() -> None:
    result = UserSpacePath(value="/documents/", user_id=42) / "report.pdf"

    assert isinstance(result, UserSpacePath)
    assert result.user_id == 42
    assert result.value == "/documents/report.pdf"
    assert result.storage_key == "user-42-files/documents/report.pdf"


@pytest.mark.parametrize("user_id", [0, -1, -100])
def test_user_space_path_rejects_invalid_user_id(
    user_id: int,
) -> None:
    with pytest.raises(ValueError):
        UserSpacePath(value="/documents/", user_id=user_id)


@pytest.mark.parametrize(
    ("value", "expected_user_id", "expected_path"),
    [
        ("user-1-files", 1, "/"),
        ("user-1-files/", 1, "/"),
        ("user-1-files/foo", 1, "/foo"),
        ("user-1-files/foo/bar.txt", 1, "/foo/bar.txt"),
        ("user-999999-files/dir", 999999, "/dir"),
    ],
)
def test_parse_valid_paths(value, expected_user_id, expected_path):
    path = UserSpacePath.from_storage_key(value)

    assert path.user_id == expected_user_id
    assert str(path.public_path) == expected_path


@pytest.mark.parametrize(
    "value",
    [
        "",
        "/",
        "user-files/",
        "user--files/",
        "user-0-files/",
        "user--1-files/",
        "user-abc-files/",
        "users-1-files/",
        "user-1-file/",
        "foo/user-1-files/",
        "/user-1-files",
        "/user-1-files/",
        "/user-1-files/foo",
        "/user-123-files/foo/bar.txt",
    ],
)
def test_parse_invalid_paths(value):
    with pytest.raises(ValueError):
        UserSpacePath.from_storage_key(value)
