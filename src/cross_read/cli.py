from __future__ import annotations

import argparse
import os

import uvicorn


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="启动 Cross Read 局域网只读文件服务")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--host", help="覆盖配置中的监听地址")
    parser.add_argument("--port", type=int, help="覆盖配置中的监听端口")
    parser.add_argument("--reload", action="store_true", help="启用开发热重载")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    os.environ["CROSS_READ_CONFIG"] = args.config

    from cross_read.core.config import load_config

    config = load_config(args.config)
    host = args.host or config.server.host
    port = args.port or config.server.port
    uvicorn.run(
        "cross_read.main:app",
        host=host,
        port=port,
        reload=args.reload,
        factory=False,
    )


if __name__ == "__main__":
    main()
