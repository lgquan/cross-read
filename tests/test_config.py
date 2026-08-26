from __future__ import annotations

from pathlib import Path

import pytest

from cross_read.core.config import AppConfig, ConfigLoadError, load_config


def test_load_config(tmp_path: Path) -> None:
    share = tmp_path / "docs"
    share.mkdir()
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"""
server:
  host: "127.0.0.1"
  port: 9000
shares:
  - id: docs
    name: 文档
    path: "{share.as_posix()}"
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert isinstance(config, AppConfig)
    assert config.server.port == 9000
    assert config.shares[0].id == "docs"


def test_duplicate_share_ids_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="共享目录 id 不能重复"):
        AppConfig.model_validate(
            {
                "shares": [
                    {"id": "docs", "name": "A", "path": str(tmp_path)},
                    {"id": "docs", "name": "B", "path": str(tmp_path)},
                ]
            }
        )


def test_missing_config_has_actionable_message(tmp_path: Path) -> None:
    with pytest.raises(ConfigLoadError, match="config.example.yaml"):
        load_config(tmp_path / "missing.yaml")


def test_windows_discovery_allows_empty_manual_share_list() -> None:
    config = AppConfig.model_validate(
        {"shares": [], "discovery": {"windows_smb": True}}
    )

    assert config.discovery.windows_smb is True


def test_config_requires_a_share_source() -> None:
    with pytest.raises(ValueError, match="至少配置一个共享目录"):
        AppConfig.model_validate({"shares": []})
