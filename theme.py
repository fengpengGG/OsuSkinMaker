"""主题样式：颜色表、主题切换与 ttk 样式配置。"""

from __future__ import annotations

import ctypes
import tkinter as tk
from tkinter import ttk


THEMES = {
    "light": {
        "name": "浅色",
        "bg": "#f5f6f8",
        "panel": "#ffffff",
        "surface": "#ffffff",
        "border": "#d8dce3",
        "text": "#1f2328",
        "text_secondary": "#5c6570",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "canvas": "#0b0b0e",
        "notebook": "#eef0f3",
        "hover": "#e8eaed",
        "selected": "#dbeafe",
        "success": "#22c55e",
        "warning": "#f59e0b",
        "danger": "#ef4444",
    },
    "dark": {
        "name": "深色",
        "bg": "#18181b",
        "panel": "#27272a",
        "surface": "#3f3f46",
        "border": "#3f3f46",
        "text": "#fafafa",
        "text_secondary": "#a1a1aa",
        "accent": "#60a5fa",
        "accent_hover": "#3b82f6",
        "canvas": "#0b0b0e",
        "notebook": "#202023",
        "hover": "#3f3f46",
        "selected": "#1e3a8a",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "danger": "#f87171",
    },
}

_CURRENT_THEME = "light"


def current_theme() -> str:
    return _CURRENT_THEME


def theme_color(key: str) -> str:
    return THEMES[_CURRENT_THEME].get(key, "#000000")


def enable_dpi_awareness() -> None:
    """Windows 高 DPI 感知，避免高分屏下界面模糊。"""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def setup_style(root: tk.Tk, theme: str = "light") -> None:
    global _CURRENT_THEME
    _CURRENT_THEME = theme if theme in THEMES else "light"
    t = THEMES[_CURRENT_THEME]

    root.option_add("*Font", ("Microsoft YaHei UI", 10))
    root.option_add("*Background", t["bg"])
    root.option_add("*Foreground", t["text"])

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # 通用
    style.configure(".", font=("Microsoft YaHei UI", 10),
                    background=t["bg"], foreground=t["text"])
    style.configure("TFrame", background=t["bg"])
    style.configure("TLabel", background=t["bg"], foreground=t["text"])
    style.configure("TCheckbutton", background=t["bg"], foreground=t["text"])
    style.configure("TRadiobutton", background=t["bg"], foreground=t["text"])

    # 按钮
    style.configure("TButton", font=("Microsoft YaHei UI", 10, "bold"),
                    padding=(10, 5), background=t["accent"], foreground="#ffffff",
                    bordercolor=t["accent"], relief="flat")
    style.map("TButton",
              background=[("active", t["accent_hover"]), ("pressed", t["accent_hover"])],
              foreground=[("active", "#ffffff")])

    # 次要按钮（图标/工具栏用）
    style.configure("Tool.TButton", font=("Microsoft YaHei UI", 9),
                    padding=(6, 3), background=t["surface"], foreground=t["text"],
                    bordercolor=t["border"])
    style.map("Tool.TButton",
              background=[("active", t["hover"])],
              foreground=[("active", t["text"])])

    # 强调主按钮（保存等主要操作）
    style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"),
                    padding=(12, 5), background=t["accent"], foreground="#ffffff",
                    bordercolor=t["accent"], relief="flat")
    style.map("Accent.TButton",
              background=[("active", t["accent_hover"]), ("pressed", t["accent_hover"])],
              foreground=[("active", "#ffffff")])

    # 标题 / 次要文本
    style.configure("Title.TLabel", font=("Microsoft YaHei UI", 11, "bold"),
                    background=t["bg"], foreground=t["text"])
    style.configure("Secondary.TLabel", font=("Microsoft YaHei UI", 9),
                    background=t["bg"], foreground=t["text_secondary"])

    # Notebook
    style.configure("TNotebook", background=t["notebook"], tabmargins=(2, 4, 2, 0))
    style.configure("TNotebook.Tab", font=("Microsoft YaHei UI", 10, "bold"),
                    padding=(14, 6), background=t["panel"], foreground=t["text_secondary"],
                    bordercolor=t["border"])
    style.map("TNotebook.Tab",
              background=[("selected", t["surface"])],
              foreground=[("selected", t["text"])],
              expand=[("selected", (2, 2, 2, 0))])

    # Labelframe / 卡片
    style.configure("TLabelframe", background=t["panel"],
                    bordercolor=t["border"], relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=t["panel"],
                    font=("Microsoft YaHei UI", 10, "bold"), foreground=t["text"])
    style.configure("Card.TFrame", background=t["panel"])
    style.configure("Card.TLabelframe", background=t["panel"], bordercolor=t["border"])
    style.configure("Card.TLabelframe.Label", background=t["panel"],
                    foreground=t["text"], font=("Microsoft YaHei UI", 10, "bold"))
    # 卡片上的标题 / 次要文本（背景与 panel 卡片一致）
    style.configure("CardTitle.TLabel", font=("Microsoft YaHei UI", 11, "bold"),
                    background=t["panel"], foreground=t["text"])
    style.configure("CardSecondary.TLabel", font=("Microsoft YaHei UI", 9),
                    background=t["panel"], foreground=t["text_secondary"])

    # Treeview
    style.configure("Treeview", rowheight=26, font=("Microsoft YaHei UI", 10),
                    background=t["panel"], foreground=t["text"], fieldbackground=t["panel"])
    style.configure("Treeview.Heading", font=("Microsoft YaHei UI", 10, "bold"),
                    background=t["surface"], foreground=t["text"])
    style.map("Treeview",
              background=[("selected", t["selected"])],
              foreground=[("selected", t["text"])])

    # 输入框
    style.configure("TEntry", fieldbackground=t["surface"], foreground=t["text"],
                    bordercolor=t["border"], insertcolor=t["text"])
    style.configure("TCombobox", fieldbackground=t["surface"], foreground=t["text"],
                    bordercolor=t["border"], selectbackground=t["selected"])
    style.map("TCombobox", fieldbackground=[("readonly", t["surface"])])

    # 滚动条
    style.configure("Vertical.TScrollbar", background=t["surface"],
                    arrowcolor=t["text"], bordercolor=t["border"],
                    troughcolor=t["bg"])

    # 分隔线
    style.configure("Line.TFrame", background=t["border"])
    style.configure("TSeparator", background=t["border"])

    # PanedWindow（sash 加宽便于拖拽；clam 下 sash 颜色随 TPanedwindow 背景）
    style.configure("TPanedwindow", background=t["bg"])
    try:
        style.configure("Sash", sashthickness=6, gripcount=0)
    except tk.TclError:
        pass

    # 滑块
    style.configure("TScale", background=t["bg"], troughcolor=t["surface"],
                    bordercolor=t["border"])