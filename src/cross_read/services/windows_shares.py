from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class WindowsShare:
    id: str
    name: str
    path: Path


class WindowsShareDiscoveryError(RuntimeError):
    """Raised when Windows SMB shares cannot be queried."""


def windows_share_id(name: str) -> str:
    digest = hashlib.sha256(name.casefold().encode("utf-8")).hexdigest()[:16]
    return f"win-{digest}"


def discover_windows_shares() -> list[WindowsShare]:
    if sys.platform != "win32":
        return []

    script = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        "Get-SmbShare | "
        "Where-Object { -not $_.Special -and $_.Path } | "
        "Select-Object Name,Path | ConvertTo-Json -Compress"
    )
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
            timeout=8,
            creationflags=creation_flags,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise WindowsShareDiscoveryError("无法读取 Windows 共享文件夹") from exc

    if not result.stdout.strip():
        return []

    try:
        raw: Any = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise WindowsShareDiscoveryError("Windows 返回的共享文件夹信息格式无效") from exc

    items = raw if isinstance(raw, list) else [raw]
    shares: list[WindowsShare] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("Name")
        path = item.get("Path")
        if not isinstance(name, str) or not name.strip():
            continue
        if not isinstance(path, str) or not path.strip():
            continue
        shares.append(
            WindowsShare(
                id=windows_share_id(name),
                name=name,
                path=Path(path),
            )
        )
    return shares
