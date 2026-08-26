from fastapi import APIRouter

from cross_read import __version__
from cross_read.models.files import StatusResponse

router = APIRouter(tags=["service"])


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    return StatusResponse(name="Cross Read", version=__version__, status="ok")
