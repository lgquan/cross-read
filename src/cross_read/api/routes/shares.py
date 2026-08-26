from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response

from cross_read.api.dependencies import get_share_registry
from cross_read.core.errors import AppError
from cross_read.core.paths import ShareRegistry
from cross_read.models.files import (
    DirectoryResponse,
    FileEntry,
    FileKind,
    ShareListResponse,
    ShareSummary,
)
from cross_read.services.file_stream import create_file_response

router = APIRouter(prefix="/shares", tags=["files"])

EXTENSION_KINDS: dict[str, FileKind] = {
    ".md": FileKind.MARKDOWN,
    ".markdown": FileKind.MARKDOWN,
    ".pdf": FileKind.PDF,
    ".docx": FileKind.DOCX,
    ".jpg": FileKind.IMAGE,
    ".jpeg": FileKind.IMAGE,
    ".png": FileKind.IMAGE,
    ".gif": FileKind.IMAGE,
    ".webp": FileKind.IMAGE,
    ".svg": FileKind.IMAGE,
    ".txt": FileKind.TEXT,
    ".log": FileKind.TEXT,
    ".json": FileKind.TEXT,
    ".yaml": FileKind.TEXT,
    ".yml": FileKind.TEXT,
    ".toml": FileKind.TEXT,
    ".py": FileKind.TEXT,
    ".js": FileKind.TEXT,
    ".ts": FileKind.TEXT,
    ".css": FileKind.TEXT,
    ".html": FileKind.TEXT,
    ".mp4": FileKind.VIDEO,
    ".mov": FileKind.VIDEO,
    ".m4v": FileKind.VIDEO,
}


def detect_file_kind(path: Path) -> FileKind:
    if path.is_dir():
        return FileKind.DIRECTORY
    return EXTENSION_KINDS.get(path.suffix.lower(), FileKind.UNSUPPORTED)


def to_client_path(parent: str, name: str) -> str:
    return f"{parent.rstrip('/')}/{name}".lstrip("/")


def to_entry(path: Path, client_path: str) -> FileEntry:
    try:
        stat = path.stat()
    except OSError:
        raise AppError(403, "path_unavailable", "无法读取文件信息") from None
    is_directory = path.is_dir()
    return FileEntry(
        name=path.name,
        path=client_path,
        kind=detect_file_kind(path),
        is_directory=is_directory,
        size=None if is_directory else stat.st_size,
        modified_at=stat.st_mtime,
    )


def resolve_file(registry: ShareRegistry, share_id: str, path: str) -> Path:
    file_path = registry.resolve(share_id, path)
    if not file_path.is_file():
        raise AppError(400, "not_a_file", "指定路径不是文件")
    return file_path


@router.get("", response_model=ShareListResponse)
def list_shares(
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
) -> ShareListResponse:
    registry.refresh_discovered()
    return ShareListResponse(
        items=[ShareSummary(id=share.id, name=share.name) for share in registry.all()]
    )


@router.get("/{share_id}/entries", response_model=DirectoryResponse)
def list_entries(
    share_id: str,
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
    path: Annotated[str, Query(max_length=4096)] = "",
) -> DirectoryResponse:
    share = registry.get(share_id)
    directory = registry.resolve(share_id, path)
    if not directory.is_dir():
        raise AppError(400, "not_a_directory", "指定路径不是文件夹")

    entries: list[FileEntry] = []
    try:
        children = list(directory.iterdir())
    except OSError:
        raise AppError(403, "directory_unavailable", "无法读取该文件夹") from None

    for child in children:
        if not registry.is_visible(child):
            continue
        child_path = to_client_path(path, child.name)
        try:
            safe_child = registry.resolve(share_id, child_path)
            entries.append(to_entry(safe_child, child_path))
        except AppError:
            # Do not expose links or junctions that escape the configured share.
            continue

    entries.sort(key=lambda entry: (not entry.is_directory, entry.name.casefold()))
    return DirectoryResponse(
        share=ShareSummary(id=share.id, name=share.name),
        path=path.strip("/"),
        items=entries,
    )


@router.api_route("/{share_id}/content", methods=["GET", "HEAD"], response_class=Response)
def read_content(
    request: Request,
    share_id: str,
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
    path: Annotated[str, Query(min_length=1, max_length=4096)],
) -> Response:
    file_path = resolve_file(registry, share_id, path)
    if detect_file_kind(file_path) is FileKind.VIDEO:
        raise AppError(400, "use_media_endpoint", "视频文件需要使用媒体播放接口")
    return create_file_response(request, file_path)


@router.api_route("/{share_id}/media", methods=["GET", "HEAD"], response_class=Response)
def stream_media(
    request: Request,
    share_id: str,
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
    path: Annotated[str, Query(min_length=1, max_length=4096)],
) -> Response:
    file_path = resolve_file(registry, share_id, path)
    if detect_file_kind(file_path) is not FileKind.VIDEO:
        raise AppError(400, "not_media", "指定文件不是支持的视频格式")
    return create_file_response(request, file_path)
