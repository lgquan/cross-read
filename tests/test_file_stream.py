import pytest

from cross_read.core.errors import AppError
from cross_read.services.file_stream import ByteRange, parse_range


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("bytes=0-0", ByteRange(0, 0)),
        ("bytes=2-5", ByteRange(2, 5)),
        ("bytes=7-", ByteRange(7, 9)),
        ("bytes=-4", ByteRange(6, 9)),
        ("bytes=-99", ByteRange(0, 9)),
        ("bytes=0-99", ByteRange(0, 9)),
    ],
)
def test_parse_range(value: str, expected: ByteRange) -> None:
    assert parse_range(value, 10) == expected


@pytest.mark.parametrize(
    "value",
    ["items=0-1", "bytes=", "bytes=5-3", "bytes=10-", "bytes=0-1,3-4", "bytes=-0"],
)
def test_parse_range_rejects_invalid_values(value: str) -> None:
    with pytest.raises(AppError) as captured:
        parse_range(value, 10)

    assert captured.value.status_code == 416
