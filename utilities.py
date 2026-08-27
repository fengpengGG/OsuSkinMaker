"""通用工具函数：文本读取/编码检测、颜色解析、数值解析。

与 tkinter 无关的纯函数，供各界面模块复用。
"""

from __future__ import annotations

import os


def read_text_file(path: str) -> str:
    """以多种编码尝试读取文本，兼容 UTF-8 / UTF-8 BOM / GBK / ANSI。"""
    enc = detect_encoding(path)
    with open(path, "r", encoding=enc) as f:
        return f.read()


def detect_encoding(path: str) -> str:
    """检测皮肤文本（skin.ini）的编码，供保存时写回同一编码，避免中文乱码。

    优先级：UTF-8(含 BOM) → GBK → latin-1（latin-1 永远可解，作兜底）。
    """
    for enc in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                f.read()
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"


# ---------------------------------------------------------------------------
# 颜色解析
# ---------------------------------------------------------------------------

def parse_rgb(text: str):
    """解析 'R,G,B' 为 (r,g,b) 0-255，失败返回 None。"""
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 3:
        try:
            return tuple(max(0, min(255, int(float(p)))) for p in parts[:3])
        except ValueError:
            return None
    return None


def rgb_to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(rgb)


# ---------------------------------------------------------------------------
# 数值解析
# ---------------------------------------------------------------------------

def _num(s, default=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _choice(s, default):
    """choice 字段值转数值：兼容 '0=拉伸' 标签文本与纯 '0' 枚举值。"""
    s = str(s).split("=", 1)[0].strip()
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def _num_list(s, default, count):
    parts = [p.strip() for p in str(s).split(",")] if s else []
    out = []
    for i in range(count):
        if i < len(parts) and parts[i]:
            out.append(_num(parts[i], default))
        else:
            out.append(default)
    return out