from __future__ import annotations

from fastapi import Request

from cross_read.core.paths import ShareRegistry


def get_share_registry(request: Request) -> ShareRegistry:
    return request.app.state.share_registry
