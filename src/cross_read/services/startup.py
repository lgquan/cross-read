from __future__ import annotations

import subprocess
import sys
from contextlib import suppress

from cross_read.core.errors import AppError

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "CrossRead"


def _registry():
    if sys.platform != "win32":
        return None
    import winreg

    return winreg


def _command() -> str:
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([sys.executable])
    return subprocess.list2cmdline([sys.executable, "-m", "cross_read.desktop"])


def can_change_startup(remote_host: str | None) -> bool:
    return sys.platform == "win32" and remote_host in {None, "127.0.0.1", "::1", "localhost"}


def is_startup_enabled() -> bool:
    winreg = _registry()
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, RUN_VALUE)
    except (FileNotFoundError, OSError):
        return False
    return bool(value)


def set_startup_enabled(enabled: bool, *, remote_host: str | None) -> bool:
    if not can_change_startup(remote_host):
        raise AppError(403, "local_only", "开机自启动只能在 Cross Read 桌面窗口中设置")

    winreg = _registry()
    if winreg is None:
        raise AppError(400, "windows_only", "开机自启动仅支持 Windows")

    try:
        if enabled:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, RUN_VALUE, 0, winreg.REG_SZ, _command())
        else:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key, suppress(FileNotFoundError):
                winreg.DeleteValue(key, RUN_VALUE)
    except OSError as exc:
        raise AppError(500, "startup_update_failed", "无法更新开机自启动设置") from exc
    return is_startup_enabled()
