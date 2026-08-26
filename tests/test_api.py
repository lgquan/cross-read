from __future__ import annotations

from fastapi.testclient import TestClient


def test_status(client: TestClient) -> None:
    response = client.get("/api/v1/status")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_shares_does_not_expose_real_path(client: TestClient) -> None:
    response = client.get("/api/v1/shares")

    assert response.status_code == 200
    assert response.json() == {"items": [{"id": "library", "name": "我的资料"}]}
    assert "path" not in response.text


def test_list_entries_orders_directories_first_and_hides_ignored(client: TestClient) -> None:
    response = client.get("/api/v1/shares/library/entries")

    assert response.status_code == 200
    body = response.json()
    assert [item["name"] for item in body["items"]] == ["资料", "notes.txt", "video.mp4"]
    assert body["items"][0]["kind"] == "directory"
    assert body["items"][1]["kind"] == "text"
    assert body["items"][2]["kind"] == "video"
    assert all(item["name"] != ".hidden.txt" for item in body["items"])


def test_list_nested_directory_with_unicode(client: TestClient) -> None:
    response = client.get("/api/v1/shares/library/entries", params={"path": "资料"})

    assert response.status_code == 200
    assert response.json()["items"][0]["path"] == "资料/readme.md"


def test_path_traversal_returns_stable_error(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/entries", params={"path": "../outside"}
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "path_outside_share",
            "message": "不允许访问共享目录之外的路径",
        }
    }


def test_file_path_cannot_be_listed_as_directory(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/entries", params={"path": "notes.txt"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "not_a_directory"


def test_read_text_content(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/content", params={"path": "资料/readme.md"}
    )

    assert response.status_code == 200
    assert response.text == "# Hello"
    assert response.headers["content-type"].startswith("text/markdown")
    assert response.headers["x-content-type-options"] == "nosniff"


def test_video_requires_media_endpoint(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/content", params={"path": "video.mp4"}
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "use_media_endpoint"


def test_media_supports_open_ended_range(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/media",
        params={"path": "video.mp4"},
        headers={"Range": "bytes=4-"},
    )

    assert response.status_code == 206
    assert response.content == b"456789"
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-range"] == "bytes 4-9/10"
    assert response.headers["content-length"] == "6"


def test_media_supports_suffix_range(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/media",
        params={"path": "video.mp4"},
        headers={"Range": "bytes=-3"},
    )

    assert response.status_code == 206
    assert response.content == b"789"


def test_invalid_media_range_returns_416(client: TestClient) -> None:
    response = client.get(
        "/api/v1/shares/library/media",
        params={"path": "video.mp4"},
        headers={"Range": "bytes=20-30"},
    )

    assert response.status_code == 416
    assert response.headers["content-range"] == "bytes */10"
    assert response.json()["error"]["code"] == "invalid_range"


def test_media_head_returns_metadata_without_body(client: TestClient) -> None:
    response = client.head(
        "/api/v1/shares/library/media", params={"path": "video.mp4"}
    )

    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["content-length"] == "10"
