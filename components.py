"""可复用 UI 组件：滚动容器、颜色工具、数字字体后缀常量。

独立于 skin.ini 表单逻辑，供各界面模块复用（通用表单 Form 保留在 gui.py，
因其与 ManiaEditor/App 深度耦合）。
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, colorchooser

from utilities import parse_rgb, rgb_to_hex
from theme import theme_color


# ---------------------------------------------------------------------------
# 滚动容器
# ---------------------------------------------------------------------------

class ScrollableFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=theme_color("bg"),
                                highlightthickness=0, borderwidth=0)
        self.canvas._is_scroll_canvas = True
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.inner = ttk.Frame(self.canvas)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(
            self._win, width=e.width))
        for w in (self.canvas, self.inner):
            w.bind("<Enter>", self._bind_wheel)
            w.bind("<Leave>", self._unbind_wheel)

    def _bind_wheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


# ---------------------------------------------------------------------------
# 颜色工具
# ---------------------------------------------------------------------------

def pick_color(var: tk.StringVar, swatch: tk.Label, has_alpha: bool) -> None:
    rgb = parse_rgb(var.get())
    initial = rgb_to_hex(rgb) if rgb else None
    _, hexval = colorchooser.askcolor(color=initial, parent=swatch)
    if hexval:
        r, g, b = int(hexval[1:3], 16), int(hexval[3:5], 16), int(hexval[5:7], 16)
        if has_alpha:
            parts = [p.strip() for p in var.get().split(",")]
            if len(parts) >= 4:
                var.set(f"{r},{g},{b},{parts[3]}")
            else:
                var.set(f"{r},{g},{b},255")
        else:
            var.set(f"{r},{g},{b}")


def apply_swatch(swatch: tk.Label, text: str) -> None:
    rgb = parse_rgb(text)
    swatch.configure(bg=rgb_to_hex(rgb) if rgb else "#ffffff")


# ---------------------------------------------------------------------------
# 数字字体后缀集合（osu! 官方）：0-9、percent、comma、dot、x
# 浏览选择 score-3.png 时，据此识别数字字体并把同组文件一并复制
# ---------------------------------------------------------------------------

FONT_SUFFIXES = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
                 "percent", "comma", "dot", "x"}