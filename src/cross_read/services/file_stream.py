from __future__ import annotations

import mimetypes
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from fastapi import Request, Response
from fastapi.responses import StreamingResponse

from cross_read.core.errors import AppError

CHUNK_SIZE = 1024 * 1024
RANGE_PATTERN = re.compile(r"^bytes=(\d*)-(\d*)$")

MIME_OVERRIDES = {
    ".md": "text/markdown; charset=utf-8",
    ".markdown": "text/markdown; charset=utf-8",
    ".jsonl": "application/x-ndjson; charset=utf-8",
    ".csv": "text/csv; charset=utf-8",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".mov": "video/quicktime",
    ".m4v": "video/x-m4v",
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".opus": "audio/ogg",
    ".svg": "image/svg+xml",
    ".yaml": "text/yaml; charset=utf-8",
    ".yml": "text/yaml; charset=utf-8",
}


@dataclass(frozen=True, slots=True)
class ByteRange:
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


def detect_mime_type(path: Path) -> str:
    override = MIME_OVERRIDES.get(path.suffix.lower())
    if override:
        return override
    guessed, _encoding = mimetypes.guess_type(path.name)
    if guessed is None:
        return "application/octet-stream"
    if guessed.startswith("text/"):
        return f"{guessed}; charset=utf-8"
    return guessed


def parse_range(value: str, file_size: int) -> ByteRange:
    match = RANGE_PATTERN.fullmatch(value.strip())
    if match is None or file_size <= 0:
        raise _range_error(file_size)

    start_text, end_text = match.groups()
    if not start_text and not end_text:
        raise _range_error(file_size)

    if not start_text:
        suffix_length = int(end_text)
        if suffix_length <= 0:
            raise _range_error(file_size)
        start = max(file_size - suffix_length, 0)
        return ByteRange(start=start, end=file_size - 1)

    start = int(start_text)
    if start >= file_size:
        raise _range_error(file_size)

    end = file_size - 1 if not end_text else min(int(end_text), file_size - 1)
    if end < start:
        raise _range_error(file_size)
    return ByteRange(start=start, end=end)


def _range_error(file_size: int) -> AppError:
    return AppError(
        416,
        "invalid_range",
        "请求的文件区间无效",
        headers={"Content-Range": f"bytes */{file_size}"},
    )


def iterate_file(path: Path, byte_range: ByteRange) -> Iterator[bytes]:
    remaining = byte_range.length
    with path.open("rb") as stream:
        stream.seek(byte_range.start)
        while remaining > 0:
            chunk = stream.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk


def create_file_response(request: Request, path: Path) -> Response:
    try:
        file_size = path.stat().st_size
    except OSError:
        raise AppError(403, "file_unavailable", "无法读取该文件") from None

    requested_range = request.headers.get("range")
    byte_range = (
        parse_range(requested_range, file_size)
        if requested_range
        else ByteRange(start=0, end=max(file_size - 1, -1))
    )
    is_partial = requested_range is not None
    content_length = byte_range.length if file_size > 0 else 0

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
        "Content-Disposition": f"inline; filename*=UTF-8''{quote(path.name)}",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, max-age=0, must-revalidate",
    }
    if is_partial:
        headers["Content-Range"] = f"bytes {byte_range.start}-{byte_range.end}/{file_size}"

    status_code = 206 if is_partial else 200
    if request.method == "HEAD" or file_size == 0:
        return Response(
            status_code=status_code,
            media_type=detect_mime_type(path),
            headers=headers,
        )

    return StreamingResponse(
        iterate_file(path, byte_range),
        status_code=status_code,
        media_type=detect_mime_type(path),
        headers=headers,
    )
