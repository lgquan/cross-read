from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class FileKind(StrEnum):
    DIRECTORY = "directory"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    UNSUPPORTED = "unsupported"


class ShareSummary(BaseModel):
    id: str
    name: str


class ShareListResponse(BaseModel):
    items: list[ShareSummary]


class FileEntry(BaseModel):
    name: str
    path: str
    kind: FileKind
    is_directory: bool
    size: int | None
    modified_at: datetime


class DirectoryResponse(BaseModel):
    share: ShareSummary
    path: str
    items: list[FileEntry]


class SearchResponse(BaseModel):
    share: ShareSummary
    path: str
    query: str
    items: list[FileEntry]
    truncated: bool = False


class StatusResponse(BaseModel):
    name: str
    version: str
    status: str
