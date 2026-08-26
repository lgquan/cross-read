from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cross_read.core.config import AppConfig
from cross_read.core.paths import ShareRegistry
from cross_read.services import windows_shares
from cross_read.services.windows_shares import (
    WindowsShare,
    WindowsShareDiscoveryError,
    discover_windows_shares,
    windows_share_id,
)


def test_windows_share_id_is_stable_and_url_safe() -> None:
    assert windows_share_id("面试项目") == windows_share_id("面试项目")
    assert windows_share_id("ATGUIGU") == windows_share_id("atguigu")
    assert windows_share_id("面试项目").startswith("win-")
    assert windows_share_id("面试项目").isascii()


def test_discover_windows_shares_parses_unicode_json(monkeypatch: pytest.MonkeyPatch) -> None:
    output = (
        '[{"Name":"atguigu","Path":"D:\\\\Courses"},'
        '{"Name":"面试项目","Path":"D:\\\\面试项目"}]'
    )

    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=[], returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(windows_shares.subprocess, "run", fake_run)
    monkeypatch.setattr(windows_shares.sys, "platform", "win32")

    shares = discover_windows_shares()

    assert [share.name for share in shares] == ["atguigu", "面试项目"]
    assert shares[1].path == Path("D:/面试项目")


def test_discovery_wraps_powershell_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd="powershell", timeout=8)

    monkeypatch.setattr(windows_shares.subprocess, "run", fake_run)
    monkeypatch.setattr(windows_shares.sys, "platform", "win32")

    with pytest.raises(WindowsShareDiscoveryError):
        discover_windows_shares()


def test_registry_refreshes_dynamic_shares(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    discovered = [WindowsShare(id="win-first", name="第一个", path=first)]

    def loader() -> list[WindowsShare]:
        return discovered.copy()

    registry = ShareRegistry(
        AppConfig.model_validate({"discovery": {"windows_smb": True}}),
        windows_share_loader=loader,
    )
    assert [share.name for share in registry.all()] == ["第一个"]

    discovered[:] = [WindowsShare(id="win-second", name="第二个", path=second)]
    registry.refresh_discovered()

    assert [share.name for share in registry.all()] == ["第二个"]


def test_registry_keeps_last_result_when_refresh_fails(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    shared.mkdir()
    should_fail = False

    def loader() -> list[WindowsShare]:
        if should_fail:
            raise WindowsShareDiscoveryError("暂时无法读取")
        return [WindowsShare(id="win-share", name="资料", path=shared)]

    registry = ShareRegistry(
        AppConfig.model_validate({"discovery": {"windows_smb": True}}),
        windows_share_loader=loader,
    )
    should_fail = True
    registry.refresh_discovered()

    assert [share.name for share in registry.all()] == ["资料"]
    assert registry.discovery_error == "暂时无法读取"
