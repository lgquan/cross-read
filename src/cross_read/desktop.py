from __future__ import annotations

import ctypes
import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pystray
import uvicorn
import webview
from PIL import Image, ImageDraw

from cross_read.core.config import load_config

APP_NAME = "Cross Read"
APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / APP_NAME
CONFIG_NAME = "config.yaml"
ERROR_ALREADY_EXISTS = 183
_instance_mutex: int | None = None


def bundled_file(name: str) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / name  # type: ignore[attr-defined]
    return Path(__file__).resolve().parents[2] / name


def ensure_config() -> Path:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config_path = APP_DATA_DIR / CONFIG_NAME
    if not config_path.exists():
        shutil.copyfile(bundled_file("config.example.yaml"), config_path)
    return config_path


def make_tray_image() -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 122, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((10, 12, 54, 52), radius=9, fill=(255, 255, 255, 245))
    draw.line((32, 12, 32, 52), fill=(0, 122, 255, 255), width=3)
    draw.line((18, 22, 27, 22), fill=(0, 122, 255, 255), width=3)
    draw.line((37, 22, 46, 22), fill=(0, 122, 255, 255), width=3)
    return image


def show_message(message: str, *, error: bool = False) -> None:
    if sys.platform != "win32":
        return
    icon = 0x10 if error else 0x40
    ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, icon)  # type: ignore[attr-defined]


def acquire_single_instance() -> bool:
    global _instance_mutex
    if sys.platform != "win32":
        return True
    _instance_mutex = ctypes.windll.kernel32.CreateMutexW(  # type: ignore[attr-defined]
        None,
        False,
        "Local\\CrossReadDesktop",
    )
    return ctypes.get_last_error() != ERROR_ALREADY_EXISTS


class DesktopApplication:
    def __init__(self) -> None:
        self.config_path = ensure_config()
        os.environ["CROSS_READ_CONFIG"] = str(self.config_path)
        self.config = load_config(self.config_path)
        self.server: uvicorn.Server | None = None
        self.window: webview.Window | None = None
        self.tray: pystray.Icon | None = None
        self.allow_close = False

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.config.server.port}"

    def start_server(self) -> None:
        server_config = uvicorn.Config(
            "cross_read.main:app",
            host=self.config.server.host,
            port=self.config.server.port,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(server_config)
        self.server.run()

    def wait_until_ready(self, timeout: float = 12.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{self.url}/api/v1/status", timeout=0.5) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError):
                time.sleep(0.1)
        raise RuntimeError("Cross Read 服务启动超时，请检查端口或配置文件")

    def show_window(self, _icon: pystray.Icon | None = None, _item: object | None = None) -> None:
        if self.window is not None:
            self.window.show()

    def hide_window(self) -> bool:
        if self.allow_close:
            return True
        if self.window is not None:
            self.window.hide()
        return False

    def exit(self, icon: pystray.Icon, _item: object | None = None) -> None:
        self.allow_close = True
        if self.window is not None:
            self.window.destroy()
        if self.server is not None:
            self.server.should_exit = True
        icon.stop()

    def run_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("打开 Cross Read", self.show_window, default=True),
            pystray.MenuItem("退出", self.exit),
        )
        self.tray = pystray.Icon(APP_NAME, make_tray_image(), APP_NAME, menu)
        self.tray.run()

    def run(self) -> None:
        server_thread = threading.Thread(
            target=self.start_server,
            name="cross-read-server",
            daemon=True,
        )
        server_thread.start()
        self.wait_until_ready()

        self.window = webview.create_window(
            APP_NAME,
            self.url,
            width=1200,
            height=820,
            min_size=(720, 520),
            background_color="#f5f5f7",
        )
        self.window.events.closing += self.hide_window
        threading.Thread(target=self.run_tray, name="cross-read-tray", daemon=True).start()
        webview.start(debug=False)


def main() -> None:
    if not acquire_single_instance():
        show_message("Cross Read 已经在运行，请在系统托盘中打开。")
        return
    try:
        DesktopApplication().run()
    except Exception as exc:
        show_message(f"Cross Read 启动失败：\n{exc}", error=True)


if __name__ == "__main__":
    main()
