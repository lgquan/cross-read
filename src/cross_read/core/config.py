from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

ShareId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9_-]{0,63}$")]


class ServerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)


class ShareConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: ShareId
    name: str = Field(min_length=1, max_length=100)
    path: Path


class VisibilityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    show_hidden: bool = False
    ignored_names: set[str] = Field(default_factory=lambda: {".git", "__pycache__"})


class DiscoveryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    windows_smb: bool = False


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    server: ServerConfig = Field(default_factory=ServerConfig)
    shares: list[ShareConfig] = Field(default_factory=list)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    visibility: VisibilityConfig = Field(default_factory=VisibilityConfig)

    @model_validator(mode="after")
    def share_ids_must_be_unique(self) -> AppConfig:
        ids = [share.id for share in self.shares]
        if len(ids) != len(set(ids)):
            raise ValueError("共享目录 id 不能重复")
        if not self.shares and not self.discovery.windows_smb:
            raise ValueError("至少配置一个共享目录，或启用 Windows SMB 自动发现")
        return self


class ConfigLoadError(RuntimeError):
    """Raised when the user configuration cannot be loaded."""


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).expanduser()
    if not config_path.is_file():
        raise ConfigLoadError(
            f"找不到配置文件：{config_path}。请复制 config.example.yaml 为 config.yaml 后修改。"
        )

    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigLoadError(f"无法读取配置文件 {config_path}：{exc}") from exc

    if raw is None:
        raise ConfigLoadError(f"配置文件 {config_path} 不能为空")

    try:
        return AppConfig.model_validate(raw)
    except ValidationError as exc:
        raise ConfigLoadError(f"配置文件 {config_path} 格式无效：\n{exc}") from exc
