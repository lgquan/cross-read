from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from cross_read.core.config import AppConfig, ShareConfig
from cross_read.core.errors import AppError
from cross_read.services.windows_shares import (
    WindowsShare,
    WindowsShareDiscoveryError,
    discover_windows_shares,
)


@dataclass(frozen=True, slots=True)
class RegisteredShare:
    id: str
    name: str
    root: Path


class ShareRegistry:
    def __init__(
        self,
        config: AppConfig,
        windows_share_loader: Callable[[], list[WindowsShare]] = discover_windows_shares,
    ) -> None:
        shares: dict[str, RegisteredShare] = {}
        for item in config.shares:
            root = self._validate_root(item)
            shares[item.id] = RegisteredShare(id=item.id, name=item.name, root=root)
        self._configured_shares = shares
        self._shares = shares.copy()
        self._windows_smb_enabled = config.discovery.windows_smb
        self._windows_share_loader = windows_share_loader
        self.discovery_error: str | None = None
        self.visibility = config.visibility
        self.refresh_discovered()

    @staticmethod
    def _validate_root(share: ShareConfig) -> Path:
        try:
            root = share.path.expanduser().resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise RuntimeError(f"共享目录“{share.name}”不存在或无法访问") from exc
        if not root.is_dir():
            raise RuntimeError(f"共享路径“{share.name}”不是文件夹")
        return root

    def all(self) -> tuple[RegisteredShare, ...]:
        return tuple(self._shares.values())

    def refresh_discovered(self) -> None:
        if not self._windows_smb_enabled:
            return

        shares = self._configured_shares.copy()
        try:
            discovered = self._windows_share_loader()
        except WindowsShareDiscoveryError as exc:
            self.discovery_error = str(exc)
            return

        for item in discovered:
            if item.id in shares:
                continue
            try:
                root = item.path.expanduser().resolve(strict=True)
            except (OSError, RuntimeError):
                continue
            if not root.is_dir():
                continue
            shares[item.id] = RegisteredShare(id=item.id, name=item.name, root=root)
        self.discovery_error = None
        self._shares = shares

    def get(self, share_id: str) -> RegisteredShare:
        share = self._shares.get(share_id)
        if share is None:
            raise AppError(404, "share_not_found", "共享目录不存在")
        return share

    def resolve(self, share_id: str, relative_path: str = "", *, must_exist: bool = True) -> Path:
        share = self.get(share_id)
        safe_relative = self._validate_relative_path(relative_path)

        try:
            candidate = (share.root / Path(*safe_relative.parts)).resolve(strict=must_exist)
        except (FileNotFoundError, NotADirectoryError):
            raise AppError(404, "file_not_found", "文件或目录不存在") from None
        except (OSError, RuntimeError):
            raise AppError(403, "path_unavailable", "无法访问该路径") from None

        if not candidate.is_relative_to(share.root):
            raise AppError(403, "path_outside_share", "不允许访问共享目录之外的路径")
        return candidate

    @staticmethod
    def _validate_relative_path(relative_path: str) -> PurePosixPath:
        if "\x00" in relative_path:
            raise AppError(400, "invalid_path", "路径格式无效")
        if "\\" in relative_path:
            raise AppError(400, "invalid_path", "路径必须使用正斜杠")

        path = PurePosixPath(relative_path)
        if path.is_absolute() or any(part == ".." for part in path.parts):
            raise AppError(403, "path_outside_share", "不允许访问共享目录之外的路径")
        if path.parts and ":" in path.parts[0]:
            raise AppError(400, "invalid_path", "路径格式无效")
        return path

    def is_visible(self, path: Path) -> bool:
        name = path.name
        if name in self.visibility.ignored_names:
            return False
        return self.visibility.show_hidden or not name.startswith(".")
