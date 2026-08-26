from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cross_read.core.config import AppConfig, ShareConfig
from cross_read.main import create_app


@pytest.fixture
def shared_dir(tmp_path: Path) -> Path:
    root = tmp_path / "shared"
    root.mkdir()
    (root / "资料").mkdir()
    (root / "资料" / "readme.md").write_text("# Hello", encoding="utf-8")
    (root / "video.mp4").write_bytes(b"0123456789")
    (root / "notes.txt").write_text("notes", encoding="utf-8")
    (root / ".hidden.txt").write_text("secret", encoding="utf-8")
    (root / "__pycache__").mkdir()
    return root


@pytest.fixture
def app_config(shared_dir: Path) -> AppConfig:
    return AppConfig(
        shares=[ShareConfig(id="library", name="我的资料", path=shared_dir)]
    )


@pytest.fixture
def client(app_config: AppConfig) -> Iterator[TestClient]:
    with TestClient(create_app(app_config)) as test_client:
        yield test_client
