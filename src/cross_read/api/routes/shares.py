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
    SearchResponse,
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
    ".xlsx": FileKind.SPREADSHEET,
    ".csv": FileKind.SPREADSHEET,
    ".pptx": FileKind.PRESENTATION,
    ".jpg": FileKind.IMAGE,
    ".jpeg": FileKind.IMAGE,
    ".png": FileKind.IMAGE,
    ".gif": FileKind.IMAGE,
    ".webp": FileKind.IMAGE,
    ".svg": FileKind.IMAGE,
    ".txt": FileKind.TEXT,
    ".log": FileKind.TEXT,
    ".json": FileKind.TEXT,
    ".jsonl": FileKind.TEXT,
    ".yaml": FileKind.TEXT,
    ".yml": FileKind.TEXT,
    ".toml": FileKind.TEXT,
    ".py": FileKind.TEXT,
    ".pyw": FileKind.TEXT,
    ".js": FileKind.TEXT,
    ".jsx": FileKind.TEXT,
    ".mjs": FileKind.TEXT,
    ".cjs": FileKind.TEXT,
    ".ts": FileKind.TEXT,
    ".tsx": FileKind.TEXT,
    ".mts": FileKind.TEXT,
    ".cts": FileKind.TEXT,
    ".css": FileKind.TEXT,
    ".html": FileKind.TEXT,
    ".htm": FileKind.TEXT,
    ".xml": FileKind.TEXT,
    ".vue": FileKind.TEXT,
    ".sh": FileKind.TEXT,
    ".bash": FileKind.TEXT,
    ".zsh": FileKind.TEXT,
    ".ps1": FileKind.TEXT,
    ".psm1": FileKind.TEXT,
    ".psd1": FileKind.TEXT,
    ".sql": FileKind.TEXT,
    ".ini": FileKind.TEXT,
    ".cfg": FileKind.TEXT,
    ".conf": FileKind.TEXT,
    ".c": FileKind.TEXT,
    ".h": FileKind.TEXT,
    ".cc": FileKind.TEXT,
    ".cpp": FileKind.TEXT,
    ".cxx": FileKind.TEXT,
    ".hpp": FileKind.TEXT,
    ".java": FileKind.TEXT,
    ".go": FileKind.TEXT,
    ".rs": FileKind.TEXT,
    ".wav": FileKind.AUDIO,
    ".mp3": FileKind.AUDIO,
    ".m4a": FileKind.AUDIO,
    ".aac": FileKind.AUDIO,
    ".flac": FileKind.AUDIO,
    ".ogg": FileKind.AUDIO,
    ".opus": FileKind.AUDIO,
    ".mp4": FileKind.VIDEO,
    ".mov": FileKind.VIDEO,
    ".m4v": FileKind.VIDEO,
}

SEARCH_MAX_RESULTS = 500
SEARCH_MAX_DIRECTORIES = 10_000


def detect_file_kind(path: Path) -> FileKind:
    if path.is_dir():
        return FileKind.DIRECTORY
    if path.name.casefold() == "dockerfile":
        return FileKind.TEXT
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


@router.get("/{share_id}/search", response_model=SearchResponse)
def search_entries(
    share_id: str,
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
    query: Annotated[str, Query(min_length=1, max_length=256, alias="q")],
    path: Annotated[str, Query(max_length=4096)] = "",
) -> SearchResponse:
    share = registry.get(share_id)
    directory = registry.resolve(share_id, path)
    if not directory.is_dir():
        raise AppError(400, "not_a_directory", "指定路径不是文件夹")

    normalized_query = query.strip().casefold()
    if not normalized_query:
        raise AppError(422, "empty_query", "搜索关键词不能为空")

    entries: list[FileEntry] = []
    stack: list[tuple[Path, str]] = [(directory, path.strip("/"))]
    visited_directories: set[Path] = set()
    truncated = False

    while stack:
        current, current_path = stack.pop()
        try:
            current = current.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if current in visited_directories:
            continue
        visited_directories.add(current)
        if len(visited_directories) > SEARCH_MAX_DIRECTORIES:
            truncated = True
            break

        try:
            children = list(current.iterdir())
        except OSError:
            continue

        for child in children:
            if not registry.is_visible(child):
                continue
            child_path = to_client_path(current_path, child.name)
            try:
                safe_child = registry.resolve(share_id, child_path)
            except AppError:
                # Do not expose links or junctions that escape the configured share.
                continue

            if normalized_query in safe_child.name.casefold():
                try:
                    entries.append(to_entry(safe_child, child_path))
                except AppError:
                    continue
                if len(entries) >= SEARCH_MAX_RESULTS:
                    truncated = True
                    break

            if safe_child.is_dir():
                stack.append((safe_child, child_path))

        if truncated:
            break

    entries.sort(key=lambda entry: (not entry.is_directory, entry.path.casefold()))
    return SearchResponse(
        share=ShareSummary(id=share.id, name=share.name),
        path=path.strip("/"),
        query=query.strip(),
        items=entries,
        truncated=truncated,
    )


@router.api_route("/{share_id}/content", methods=["GET", "HEAD"], response_class=Response)
def read_content(
    request: Request,
    share_id: str,
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
    path: Annotated[str, Query(min_length=1, max_length=4096)],
) -> Response:
    file_path = resolve_file(registry, share_id, path)
    if detect_file_kind(file_path) in {FileKind.AUDIO, FileKind.VIDEO}:
        raise AppError(400, "use_media_endpoint", "音视频文件需要使用媒体播放接口")
    return create_file_response(request, file_path)


@router.api_route("/{share_id}/media", methods=["GET", "HEAD"], response_class=Response)
def stream_media(
    request: Request,
    share_id: str,
    registry: Annotated[ShareRegistry, Depends(get_share_registry)],
    path: Annotated[str, Query(min_length=1, max_length=4096)],
) -> Response:
    file_path = resolve_file(registry, share_id, path)
    if detect_file_kind(file_path) not in {FileKind.AUDIO, FileKind.VIDEO}:
        raise AppError(400, "not_media", "指定文件不是支持的媒体格式")
    return create_file_response(request, file_path)
