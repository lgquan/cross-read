from __future__ import annotations

import os
from pathlib import Path

import pytest

from cross_read.core.config import AppConfig, ShareConfig
from cross_read.core.errors import AppError
from cross_read.core.paths import ShareRegistry


def test_resolve_file_inside_share(shared_dir: Path) -> None:
    registry = ShareRegistry(
        AppConfig(shares=[ShareConfig(id="docs", name="文档", path=shared_dir)])
    )

    result = registry.resolve("docs", "资料/readme.md")

    assert result == (shared_dir / "资料" / "readme.md").resolve()


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "../outside.txt",
        "资料/../../outside.txt",
        "/Windows/System32",
        "C:/Windows/System32",
        r"..\outside.txt",
        "bad\x00name.txt",
    ],
)
def test_rejects_unsafe_paths(shared_dir: Path, unsafe_path: str) -> None:
    registry = ShareRegistry(
        AppConfig(shares=[ShareConfig(id="docs", name="文档", path=shared_dir)])
    )

    with pytest.raises(AppError):
        registry.resolve("docs", unsafe_path)


def test_missing_share_does_not_disclose_filesystem(shared_dir: Path) -> None:
    registry = ShareRegistry(
        AppConfig(shares=[ShareConfig(id="docs", name="文档", path=shared_dir)])
    )

    with pytest.raises(AppError) as captured:
        registry.resolve("missing", "anything")

    assert captured.value.code == "share_not_found"
    assert str(shared_dir) not in captured.value.message


def test_symlink_cannot_escape_share(shared_dir: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("private", encoding="utf-8")
    link = shared_dir / "escape.txt"
    try:
        os.symlink(outside, link)
    except OSError:
        pytest.skip("当前 Windows 环境不允许创建符号链接")

    registry = ShareRegistry(
        AppConfig(shares=[ShareConfig(id="docs", name="文档", path=shared_dir)])
    )

    with pytest.raises(AppError) as captured:
        registry.resolve("docs", "escape.txt")

    assert captured.value.code == "path_outside_share"
