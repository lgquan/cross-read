from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from cross_read.models.files import StartupResponse
from cross_read.services.startup import can_change_startup, is_startup_enabled, set_startup_enabled

router = APIRouter(prefix="/system", tags=["system"])


class StartupRequest(BaseModel):
    enabled: bool


def _remote_host(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("/startup", response_model=StartupResponse)
def get_startup_setting(request: Request) -> StartupResponse:
    available = can_change_startup(_remote_host(request))
    return StartupResponse(
        enabled=is_startup_enabled(),
        available=available,
        message=None if available else "请在 Cross Read 桌面窗口中修改此设置",
    )


@router.put("/startup", response_model=StartupResponse)
def update_startup_setting(request: Request, payload: StartupRequest) -> StartupResponse:
    enabled = set_startup_enabled(payload.enabled, remote_host=_remote_host(request))
    return StartupResponse(enabled=enabled, available=True)
