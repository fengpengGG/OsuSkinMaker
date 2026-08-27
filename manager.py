"""皮肤文件夹扫描与管理。

扫描皮肤目录中的素材文件，判断 mania 元素是否存在、是否为高清（@2x）、
是否含帧动画，并给出缺失清单。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from catalog import ELEMENTS

IMAGE_EXTS = (".png", ".gif", ".jpg", ".jpeg")


def strip_hd(stem: str) -> str:
    """去掉高清后缀（``@2x`` / 历史遗留 ``2x``），保留帧号等其余部分。

    用于构建字体数字等精确查找的“主干”键，例如 ``score-3@2x`` -> ``score-3``。
    """
    low = stem.lower()
    if low.endswith("@2x"):
        return stem[:-3]
    if low.endswith("2x"):
        return stem[:-2]
    return stem


def parse_stem(stem: str) -> tuple:
    """解析文件名主干，返回 (基础名, 是否高清, 帧号或None)。

    支持 ``@2x`` 以及历史遗留的无 ``@`` 的 ``2x`` 高清后缀，
    也支持“帧号 + 2x”的组合（如 ``comboburst-02x``）。

    例如：
        mania-note1           -> ("mania-note1", False, None)
        mania-note1@2x        -> ("mania-note1", True, None)
        mania-note1-3         -> ("mania-note1", False, 3)
        mania-note1-3@2x      -> ("mania-note1", True, 3)
        mania-stage-bottom2x  -> ("mania-stage-bottom", True, None)
        comboburst-02x        -> ("comboburst", True, 0)
        hit3002x              -> ("hit300", True, None)
        comboburst-mania      -> ("comboburst-mania", False, None)
    """
    low = stem.lower()
    is_hd = False
    if low.endswith("@2x"):
        is_hd = True
        stem = stem[:-3]
    elif low.endswith("2x"):
        is_hd = True
        stem = stem[:-2]

    frame = None
    base = stem
    if "-" in stem:
        head, _, num = stem.rpartition("-")
        if num.isdigit():
            base = head
            frame = int(num)
    # 滑条球是唯一的例外：以 sliderb0 / sliderb1 ... 命名（无横杠）
    m = re.fullmatch(r"(sliderb)(\d+)", base, re.IGNORECASE)
    if m:
        return m.group(1), is_hd, int(m.group(2))
    return base, is_hd, frame


@dataclass
class ElementStatus:
    element: object
    exists: bool = False
    has_hd: bool = False
    frames: int = 0        # 动画帧数量（不含 @2x）
    files: list = field(default_factory=list)


class SkinManager:
    def __init__(self, folder: str):
        self.folder = Path(folder)
        self._base_files: dict = {}   # base -> {"paths": [...], "hd": bool, "frames": set}
        self._stem_files: dict = {}   # 相对主干（含目录、去 @2x/2x）-> 文件路径，用于字体数字等精确查找
        self._stem_plain: dict = {}   # 纯主干（不含目录、去 @2x/2x）-> 文件路径，用于默认前缀查找子目录数字

    @staticmethod
    def _norm(base: str) -> str:
        """归一化路径键：反斜杠转 /，并做大小写折叠。

        osu! 在 Windows 下对皮肤路径不区分大小写，因此 skin.ini 里
        写 ``mania/big/6`` 而实际目录是 ``Mania/big/6`` 也应能命中。
        """
        return str(base).replace("\\", "/").casefold()

    def scan(self) -> None:
        self._base_files.clear()
        self._stem_files.clear()
        self._stem_plain.clear()
        if not self.folder.is_dir():
            return
        for p in self.folder.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in IMAGE_EXTS:
                continue
            base, is_hd, frame = parse_stem(p.stem)
            # 保留相对子目录（用 / 分隔），以支持 skin.ini 里的
            # 自定义相对路径，如 NoteImage0: mania/keyC
            rel_dir = p.relative_to(self.folder).parent.as_posix()
            if rel_dir != ".":
                base = f"{rel_dir}/{base}"
            key = self._norm(base)
            info = self._base_files.setdefault(key, {"paths": [], "hd": False, "frames": set()})
            info["paths"].append(p)
            if is_hd:
                info["hd"] = True
            if frame is not None:
                info["frames"].add(frame)

            # 精确主干：去掉 @2x/2x，但保留 -N 帧号，用于字体数字等查找
            # （如 score-3、score-comma、score-percent）。
            stem = strip_hd(p.stem)
            if rel_dir != ".":
                stem = f"{rel_dir}/{stem}"
            self._stem_files.setdefault(self._norm(stem), []).append(p)
            # 纯主干（不含目录）：皮肤 Fonts 前缀默认 "score" 时，
            # 数字文件可能位于子目录（如 Fonts/score/score-3@2x.png），
            # 用纯文件名也能命中（@2x 优先由 _first_hd 保证）。
            self._stem_plain.setdefault(self._norm(strip_hd(p.stem)), []).append(p)

    # -- 查询 --------------------------------------------------------------
    @staticmethod
    def is_hd_path(path) -> bool:
        """判断文件是否为高清（@2x / 历史遗留 2x）素材。"""
        stem = Path(str(path)).stem.lower()
        return stem.endswith("@2x") or stem.endswith("2x")

    @staticmethod
    def _first_hd(paths) -> object:
        """返回最佳文件路径，优先级从高到低：

        1. @2x 且帧号为 0（动画第一帧，如 ``hit300g-0@2x.png``）
        2. 非 @2x 且帧号为 0（``hit300g-0.png``）
        3. @2x（官方 @2x > 历史遗留 2x）
        4. 非 @2x
        5. 第一个文件（兜底）

        空/None 返回 None。
        """
        if not paths:
            return None

        def _has_frame0(p):
            _, _, frame = parse_stem(Path(str(p)).stem)
            return frame == 0

        def _is_at2x(p):
            return SkinManager.is_hd_path(p) and Path(str(p)).stem.lower().endswith("@2x")

        # 1) @2x 帧 0
        for p in paths:
            if _is_at2x(p) and _has_frame0(p):
                return p
        # 2) 非 @2x 帧 0
        for p in paths:
            if not SkinManager.is_hd_path(p) and _has_frame0(p):
                return p
        # 3) @2x
        for p in paths:
            if _is_at2x(p):
                return p
        # 4) 历史遗留 2x
        for p in paths:
            if SkinManager.is_hd_path(p):
                return p
        # 5) 兜底
        return paths[0]

    def has_base(self, base: str) -> bool:
        return self._norm(base) in self._base_files or self._norm(base) in self._stem_files

    def path_for(self, base: str):
        """返回指定 base 的文件路径（大小写不敏感），优先 @2x，找不到返回 None。"""
        info = self._base_files.get(self._norm(base))
        if info and info["paths"]:
            return self._first_hd(info["paths"])
        return self.path_for_stem(base)

    def path_for_exact(self, base: str):
        """同 path_for，但不回退到 stem 模糊匹配（仅查 _base_files 精确索引）。

        用于 skin.ini 指定的路径：若 skin.ini 写了 ``mania/hit300g`` 但该文件
        不存在，不应自动回退到根目录的同名文件，否则会绕过 skin.ini 的指定意图。
        """
        info = self._base_files.get(self._norm(base))
        if info and info["paths"]:
            return self._first_hd(info["paths"])
        return None

    def path_for_stem(self, stem: str):
        """按主干查找文件（保留 -N 帧号、大小写不敏感），优先 @2x。

        先按完整前缀（含目录，如 ``Fonts/combo/combo-1``）查找；
        失败时回退到纯文件名（如 ``combo-1``），以兼容 skin.ini 前缀
        与实际文件位置不一致的情况（文件可能在根目录或其他子目录）。
        """
        key = self._norm(stem)
        paths = self._stem_files.get(key)
        if not paths:
            plain = self._norm(
                strip_hd(str(stem).replace("\\", "/").rsplit("/", 1)[-1]))
            paths = self._stem_plain.get(plain)
        return self._first_hd(paths)

    def status(self, element) -> ElementStatus:
        info = self._base_files.get(self._norm(element.filename))
        st = ElementStatus(element=element)
        if info:
            st.exists = True
            st.has_hd = info["hd"]
            st.frames = len(info["frames"])
            st.files = info["paths"]
        else:
            # 数字等精确 stem 查找（如 score-0、score-percent）
            paths = self._stem_files.get(self._norm(element.filename))
            if paths:
                st.exists = True
                st.has_hd = any(self.is_hd_path(p) for p in paths)
                st.files = paths
        return st

    def missing(self) -> list:
        """返回所有缺失的元素（按目录顺序）。"""
        return [e for e in ELEMENTS if not self.has_base(e.filename)]

    def present(self) -> list:
        return [e for e in ELEMENTS if self.has_base(e.filename)]

    def summary(self) -> dict:
        present = self.present()
        return {
            "total": len(ELEMENTS),
            "present": len(present),
            "missing": len(ELEMENTS) - len(present),
        }
