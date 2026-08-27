"""应用设置持久化（settings.json）。"""

from __future__ import annotations

import json
import os
import sys


def _settings_path() -> str:
    """配置文件路径：源码运行时在项目目录，打包 exe 时在 exe 同目录。

    统一存放在 <基础目录>/settings/settings.json。
    """
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "settings", "settings.json")


def _settings_dir() -> str:
    return os.path.dirname(_settings_path())


def load_settings() -> dict:
    """读取 settings.json；不存在或损坏时返回空字典。

    自动迁移旧位置（基础目录下）的 settings.json 到 settings 文件夹。
    """
    path = _settings_path()
    if not os.path.exists(path):
        base = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
                else os.path.dirname(os.path.abspath(__file__)))
        old = os.path.join(base, "settings.json")
        if os.path.exists(old):
            try:
                with open(old, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data = data if isinstance(data, dict) else {}
                save_settings(data)
                os.remove(old)
                return data
            except Exception:
                pass
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    """写 settings.json；失败（如无写权限）时静默忽略。"""
    try:
        os.makedirs(_settings_dir(), exist_ok=True)
        with open(_settings_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass