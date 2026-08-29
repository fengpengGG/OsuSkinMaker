"""tkinter 图形界面。

功能：
- 打开皮肤文件夹、编辑并保存 skin.ini（重点为 [Mania]）
- mania 元素浏览、缺失检测、图片预览

界面主体：ManiaEditor 编辑 skin.ini、ElementPanel 浏览皮肤元素、
StagePreview 绘制游玩舞台预览、App 主窗口编排。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from app_settings import load_settings, save_settings
from components import ScrollableFrame, pick_color, apply_swatch, FONT_SUFFIXES
from manager import SkinManager, parse_stem, strip_hd
from skin_ini import (
    SkinIni, Command, Section,
    GENERAL_COMMANDS, COLOUR_COMMANDS, FONT_COMMANDS,
    MANIA_COMMANDS, MANIA_COLUMN_COMMANDS, NOTE_LAYOUT,
)
from theme import (
    THEMES, current_theme, theme_color, enable_dpi_awareness, setup_style,
)
from utilities import (
    read_text_file, detect_encoding, parse_rgb, rgb_to_hex,
    _num, _choice, _num_list,
)

# catalog 仅 ElementPanel 使用，按需导入
from catalog import by_group, by_name, PAGE_SCREEN

try:
    from PIL import Image, ImageChops, ImageTk
    HAS_PIL = True
except Exception:
    HAS_PIL = False


# ---------------------------------------------------------------------------
# 通用表单：根据命令 schema 渲染字段（Form 与 ManiaEditor/App 深度耦合，
# 故保留在 gui.py；其余独立工具见 theme/app_settings/utilities/components）
# ---------------------------------------------------------------------------


class Form:
    """在父容器内按行渲染一组命令字段，支持 load/save/重置。"""

    def __init__(self, parent, getter, setter, skin_folder_getter=None):
        self.parent = parent
        self.getter = getter          # (key) -> str | None
        self.setter = setter          # (key, value) -> None
        self.vars = {}                # key -> tk 变量
        self._originals = {}          # key -> 从 skin.ini 加载时的原始值
        self._row = 0
        self.on_change = None         # 字段变化回调（用于实时预览）
        self._loading = False         # load() 期间不触发 on_change
        self._skin_folder_getter = skin_folder_getter  # 浏览按钮用
        self._cmd_types = {}          # key -> 命令类型（fontprefix 字段写入前缀名）
        self._choices = {}            # key -> choice 字段的显示标签元组

    def add(self, cmd: Command) -> None:
        self._cmd_types[cmd.key] = cmd.type
        ttk.Label(self.parent, text=cmd.label).grid(
            row=self._row, column=0, sticky="w", padx=(6, 4), pady=3)

        if cmd.type == "bool":
            var = tk.BooleanVar()
            w = ttk.Checkbutton(self.parent, variable=var)
            w.grid(row=self._row, column=1, sticky="w")
        elif cmd.type == "choice":
            var = tk.StringVar()
            self._choices[cmd.key] = cmd.choices
            w = ttk.Combobox(self.parent, textvariable=var,
                             values=list(cmd.choices), state="readonly", width=16)
            w.grid(row=self._row, column=1, sticky="w", padx=4)
        elif cmd.type in ("rgb", "rgba"):
            var = tk.StringVar()
            frame = ttk.Frame(self.parent)
            frame.grid(row=self._row, column=1, sticky="w", padx=4)
            ttk.Entry(frame, textvariable=var, width=16).pack(side="left")
            swatch = tk.Label(frame, width=3, relief="sunken", bg="#ffffff")
            swatch.pack(side="left", padx=4)
            ttk.Button(frame, text="选色", width=5, style="Tool.TButton",
                       command=lambda v=var, s=swatch: pick_color(v, s, cmd.type == "rgba")
                       ).pack(side="left")
            var.trace_add("write", lambda *a, s=swatch: apply_swatch(s, var.get()))
            apply_swatch(swatch, var.get())
        elif cmd.type in ("int", "number"):
            var = tk.StringVar()
            frame = ttk.Frame(self.parent)
            frame.grid(row=self._row, column=1, sticky="w", padx=4)
            ent = ttk.Entry(frame, textvariable=var, width=10)
            ent.pack(side="left")
            # 滑块：仅对典型数值范围做辅助，避免误导，范围设为 0~1000
            scale = tk.Scale(frame, from_=0, to=1000, orient="horizontal",
                             showvalue=0, length=90, sliderlength=14,
                             bg=theme_color("bg"), troughcolor=theme_color("surface"),
                             highlightthickness=0, borderwidth=0)
            scale.pack(side="left", padx=(6, 0))

            def _sync_entry(*a, v=var, s=scale):
                try:
                    s.set(float(v.get() or 0))
                except ValueError:
                    pass

            def _sync_scale(val, v=var):
                v.set(str(int(float(val))))

            var.trace_add("write", _sync_entry)
            scale.configure(command=_sync_scale)
        else:
            var = tk.StringVar()
            frame = ttk.Frame(self.parent)
            frame.grid(row=self._row, column=1, sticky="w", padx=4)
            ttk.Entry(frame, textvariable=var, width=18).pack(side="left")
            # 图片路径字段（type=="image"）与字体前缀字段（type=="fontprefix"）
            # 才提供文件浏览；普通文本字段（皮肤名称、作者等）不需要
            if cmd.type in ("image", "fontprefix") and self._skin_folder_getter:
                ttk.Button(frame, text="浏览", width=4, style="Tool.TButton",
                           command=lambda v=var: self._browse_file(v)
                           ).pack(side="left", padx=(3, 0))

        # 重置按钮
        reset = ttk.Button(self.parent, text="↺", width=2, style="Tool.TButton",
                           command=lambda k=cmd.key: self._reset_key(k))
        reset.grid(row=self._row, column=2, sticky="w", padx=(2, 6))

        self.vars[cmd.key] = var
        var.trace_add("write", lambda *a, key=cmd.key: self._on_key_change(key))
        self._row += 1

    def _reset_key(self, key: str) -> None:
        """将单个字段恢复为 skin.ini 加载时的原始值并触发刷新。"""
        var = self.vars.get(key)
        if var is None:
            return
        original = self._originals.get(key)
        if original is None:
            return
        var.set(original)
        self._on_key_change(key)

    def _browse_file(self, var):
        """点击“浏览”：按设置中的“编辑方式”把素材图片写入字段。

        - path 模式：直接写皮肤内的相对路径（原方式）
        - copy 模式：把图片复制到皮肤根目录下的指定文件夹（默认 mania），
          再写入“文件夹名/文件名”的相对路径
        """
        folder = self._skin_folder_getter() if self._skin_folder_getter else None
        if not folder:
            return
        path = filedialog.askopenfilename(
            title="选择皮肤素材",
            initialdir=folder,
            filetypes=[("图片", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")],
        )
        if not path:
            return
        # 读取“编辑方式”设置（path / copy）与目标文件夹名
        top = self.parent.winfo_toplevel()
        mode_var = getattr(top, "ini_import_mode_var", None)
        mode = mode_var.get() if mode_var else "path"
        copy_folder = "mania"
        folder_var = getattr(top, "ini_import_folder_var", None)
        if folder_var:
            name = folder_var.get().strip("/\\").strip()
            copy_folder = name if name else "mania"

        if mode == "copy":
            src_dir = os.path.dirname(path)
            bstem = strip_hd(os.path.splitext(os.path.basename(path))[0])
            prefix, _, suffix = bstem.rpartition("-")
            # 选中 score/combo 等数字字体时，把同目录同前缀的同组文件一并复制
            srcs = [path]
            if prefix and suffix.casefold() in FONT_SUFFIXES:
                try:
                    for fname in os.listdir(src_dir):
                        fpath = os.path.join(src_dir, fname)
                        if not os.path.isfile(fpath):
                            continue
                        if os.path.splitext(fname)[1].lower() not in \
                                (".png", ".jpg", ".jpeg", ".gif"):
                            continue
                        fstem = strip_hd(os.path.splitext(fname)[0])
                        p2, _, s2 = fstem.rpartition("-")
                        if p2.casefold() == prefix.casefold() and \
                                s2.casefold() in FONT_SUFFIXES:
                            srcs.append(fpath)
                except OSError:
                    srcs = [path]
            # 复制到皮肤子目录；目标已有同名文件时统一询问一次是否覆盖
            def _dest_of(src):
                return os.path.join(folder, copy_folder, os.path.basename(src))

            def _is_same_target(src):
                return os.path.normcase(os.path.abspath(_dest_of(src))) == \
                    os.path.normcase(os.path.abspath(src))

            existing = [src for src in srcs
                        if not _is_same_target(src) and os.path.exists(_dest_of(src))]
            overwrite = False
            if len(srcs) > 1 and existing:
                overwrite = messagebox.askyesno(
                    "覆盖确认",
                    f"{copy_folder}/ 中已有 {len(existing)} 个同名文件"
                    f"（如 {os.path.basename(existing[0])}）。\n"
                    "是否覆盖它们？选择“否”将跳过这些文件。")
            copied = []
            for src in srcs:
                dest = _dest_of(src)
                if not _is_same_target(src):
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    if os.path.exists(dest):
                        if len(srcs) == 1:
                            if not messagebox.askyesno(
                                    "覆盖确认",
                                    f"{copy_folder}/{os.path.basename(src)} 已存在，是否覆盖？"):
                                return
                        elif not overwrite:
                            continue  # 批量且用户选择不覆盖已有文件
                    try:
                        shutil.copy2(src, dest)
                        copied.append(os.path.basename(src))
                    except Exception as exc:
                        if len(srcs) == 1:
                            messagebox.showerror("复制失败", f"无法复制文件：{exc}")
                            return
                        continue
            if len(srcs) > 1:
                messagebox.showinfo(
                    "数字字体",
                    f"已把同组字体一并复制到 {copy_folder}/：\n"
                    + "、".join(sorted(copied)))
            rel = os.path.join(copy_folder, os.path.basename(path))
        else:
            try:
                rel = os.path.relpath(path, folder)
            except ValueError:
                return  # 不在皮肤文件夹内，忽略
            if rel.startswith(".."):
                return  # 不在皮肤文件夹内
        # 去掉扩展名，\ 转 /，再去掉 @2x/2x 后缀（osu! 在 skin.ini 中不写 @2x）
        stem = os.path.splitext(rel)[0].replace("\\", "/")
        stem = strip_hd(stem)
        # 字体前缀字段（ScorePrefix 等）：写入前缀名而非完整文件名，
        # 例如选择 font/score-3@2x.png -> 写入 font/score
        var_key = None
        for k, v in self.vars.items():
            if v is var:
                var_key = k
                break
        if var_key and self._cmd_types.get(var_key) == "fontprefix":
            pfx, _, sfx = stem.rpartition("-")
            if pfx and sfx.casefold() in FONT_SUFFIXES:
                stem = pfx
        var.set(stem)
        # 触发 on_change 回调（实时预览）
        if var_key is not None:
            self._on_key_change(var_key)

    def _value_for_key(self, key: str, text: str) -> str:
        """把控件文本转成写入 skin.ini 的值（choice 取枚举值）。"""
        text = text.strip()
        if self._cmd_types.get(key) == "choice":
            return text.split("=", 1)[0].strip()
        return text

    def _text_for_key(self, key: str, value) -> str:
        """把 skin.ini 的值转成控件文本（choice 取显示标签）。"""
        if self._cmd_types.get(key) == "choice":
            value = str(value if value is not None else "")
            for c in self._choices.get(key, ()):
                if c.split("=", 1)[0].strip() == value:
                    return c
            return value
        return value if value is not None else ""

    def _on_key_change(self, key: str) -> None:
        """字段变化：把新值提交到 ini，再触发预览刷新。

        只有绑定了 on_change 的表单才提交（避免影响 Mania 编辑器内部
        由 ManiaEditor 自己管理的表单）。
        """
        if self._loading or self.on_change is None:
            return
        var = self.vars.get(key)
        if var is None:
            return
        if isinstance(var, tk.BooleanVar):
            self.setter(key, "1" if var.get() else "0")
        else:
            self.setter(key, self._value_for_key(key, var.get()))
        self.on_change()

    def load(self) -> None:
        known = getattr(self, "_known", ())
        self._loading = True
        try:
            for key, var in self.vars.items():
                val = self.getter(key)
                # 用 schema 里的默认值兜底
                if val is None:
                    cmd = next((c for c in known if c.key == key), None)
                    val = cmd.default if cmd else ""
                if isinstance(var, tk.BooleanVar):
                    var.set(val in ("1", "true", "yes", True))
                else:
                    var.set(self._text_for_key(key, val))
                # 记录原始值（从 skin.ini 加载时的值，用于 ↺ 重置）
                self._originals[key] = var.get()
        finally:
            self._loading = False

    def save(self) -> None:
        for key, var in self.vars.items():
            if isinstance(var, tk.BooleanVar):
                self.setter(key, "1" if var.get() else "0")
            else:
                val = self._value_for_key(key, var.get())
                if val:
                    self.setter(key, val)

    def set_known(self, known: list) -> "Form":
        self._known = known
        return self


# ---------------------------------------------------------------------------
# Mania 编辑器
# ---------------------------------------------------------------------------

class ManiaEditor(ttk.Frame):
    def __init__(self, parent, ini: SkinIni, skin_folder_getter=None):
        super().__init__(parent)
        self.ini = ini
        self.current_section = None
        self.column_forms = []
        self.all_vars = {}
        self.on_change = None   # 字段变化回调（用于实时预览）
        self._loading = False
        self._skin_folder_getter = skin_folder_getter
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=(8, 6))
        ttk.Label(top, text="键数:").pack(side="left")
        self.keys_var = tk.StringVar(value="4")
        self.keys_box = ttk.Combobox(top, textvariable=self.keys_var, width=5,
                                     values=[str(k) for k in NOTE_LAYOUT.keys()],
                                     state="readonly")
        self.keys_box.pack(side="left", padx=4)
        self.keys_box.bind("<<ComboboxSelected>>", lambda e: self.reload())
        ttk.Button(top, text="重置所有", command=self.reload,
                   style="Tool.TButton").pack(side="left", padx=6)

        body = ScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.body = body.inner

        self._rebuild_forms()
        self._load()

    def _make_getter(self):
        sec = self.current_section
        return (lambda k: sec.get(k)) if sec is not None else (lambda k: None)

    def _make_setter(self):
        sec = self.current_section
        return (lambda k, v: sec.set(k, v)) if sec is not None else (lambda k, v: None)

    def _rebuild_forms(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.column_forms = []

        self.scalar_form = Form(self.body, self._make_getter(), self._make_setter(),
                                    skin_folder_getter=self._skin_folder_getter)
        self.scalar_form.set_known(MANIA_COMMANDS)

        ttk.Label(self.body, text="布局与外观", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self.scalar_form._row = 1
        for cmd in MANIA_COMMANDS:
            if cmd.key == "Keys":
                continue
            self.scalar_form.add(cmd)

        # 每列分组
        keys = int(self.keys_var.get())
        layout = NOTE_LAYOUT.get(keys, ["1"] * keys)
        ttk.Label(self.body, text="每列设置", style="Title.TLabel").grid(
            row=self.scalar_form._row, column=0, columnspan=2, sticky="w", pady=(8, 2))
        self.scalar_form._row += 1

        for n0 in range(keys):
            n1 = n0 + 1
            note = layout[n0]
            lf = ttk.LabelFrame(self.body, text=f"第 {n1} 列（默认音符 note{note}）")
            lf.grid(row=self.scalar_form._row, column=0, columnspan=2,
                    sticky="we", padx=6, pady=4)
            self.scalar_form._row += 1
            concrete = []
            for c in MANIA_COLUMN_COMMANDS:
                concrete.append(Command(
                    key=c.key.format(n0=n0, n1=n1),
                    type=c.type, label=c.label.format(n0=n0, n1=n1),
                    default=c.default, help=c.help))
            f = Form(lf, self._make_getter(), self._make_setter(),
                     skin_folder_getter=self._skin_folder_getter)
            f.set_known(concrete)
            for c in concrete:
                f.add(c)
            self.column_forms.append(f)

        self._collect_vars()
        self._attach_traces()

    def _collect_vars(self):
        self.all_vars = dict(self.scalar_form.vars)
        for f in self.column_forms:
            self.all_vars.update(f.vars)

    def _attach_traces(self):
        for var in self.all_vars.values():
            var.trace_add("write", self._on_var_change)

    def _on_var_change(self, *args):
        if not self._loading and self.on_change:
            self.on_change()

    def _notify(self):
        if self.on_change:
            self.on_change()

    def reload(self):
        keys = int(self.keys_var.get())
        sec = None
        for s in self.ini.sections_named("Mania"):
            if s.get("Keys") == str(keys):
                sec = s
                break
        self.current_section = sec
        self._loading = True
        self._rebuild_forms()
        self._load()
        self._loading = False
        self._notify()

    def _load(self):
        self.scalar_form.load()
        for f in self.column_forms:
            f.load()

    def save(self):
        keys = int(self.keys_var.get())
        self.current_section = self._ensure_section(keys)
        self.scalar_form.getter = self._make_getter()
        self.scalar_form.setter = self._make_setter()
        self.scalar_form.setter("Keys", str(keys))
        self.scalar_form.save()
        for f in self.column_forms:
            f.getter = self._make_getter()
            f.setter = self._make_setter()
            f.save()

    def _ensure_section(self, keys: int) -> Section:
        for s in self.ini.sections_named("Mania"):
            if s.get("Keys") == str(keys):
                return s
        sec = Section(name="Mania")
        self.ini.sections.append(sec)
        return sec


# ---------------------------------------------------------------------------
# 元素管理面板
# ---------------------------------------------------------------------------

class ElementPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._expand_map = {}   # iid → 节点键（group 或 "group/category"），用于记住展开/收缩
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=(8, 6))
        self.summary_var = tk.StringVar(value="未加载皮肤")
        ttk.Label(top, textvariable=self.summary_var, style="Title.TLabel").pack(side="left")

        # 筛选按钮组
        self.filter_var = tk.StringVar(value="all")
        filters = [("全部", "all"), ("缺失", "missing"), ("@2x", "hd"), ("动画", "anim")]
        for text, val in filters:
            ttk.Radiobutton(top, text=text, value=val, variable=self.filter_var,
                            command=self.refresh).pack(side="left", padx=(8, 0))

        ttk.Button(top, text="重新扫描", command=self.refresh,
                   style="Tool.TButton").pack(side="right")

        paned = self.paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(paned, style="Card.TFrame", padding=8)
        right = ttk.Frame(paned, style="Card.TFrame", padding=8)
        paned.add(left, weight=1)
        paned.add(right, weight=1)

        self.tree = ttk.Treeview(left, columns=("state",), show="tree headings")
        self.tree.heading("#0", text="元素")
        self.tree.heading("state", text="状态")
        self.tree.column("state", width=130, anchor="w")
        # 状态颜色标签
        self.tree.tag_configure("ok", foreground=theme_color("success"))
        self.tree.tag_configure("missing", foreground=theme_color("danger"))
        self.tree.tag_configure("hd", foreground=theme_color("accent"))
        self.tree.tag_configure("anim", foreground=theme_color("warning"))
        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", self._on_double_click)
        # 记住分类节点的展开/收缩状态
        self.tree.bind("<<TreeviewOpen>>", self._on_open_close)
        self.tree.bind("<<TreeviewClose>>", self._on_open_close)

        ttk.Label(right, text="预览", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 4))
        self.preview = ttk.Frame(right, style="Card.TFrame")
        self.preview.pack(fill="both", expand=True)
        self.info_var = tk.StringVar()
        # 信息区：贴底且随宽度自动换行，避免长文本溢出到屏幕外
        self.info_label = ttk.Label(right, textvariable=self.info_var, justify="left",
                                    style="CardSecondary.TLabel", anchor="w",
                                    wraplength=300)
        self.info_label.pack(side="bottom", anchor="w", fill="x", pady=(4, 0))
        self.info_label.bind("<Configure>",
                             lambda ev: self.info_label.configure(
                                 wraplength=max(120, ev.width - 24)))

    def refresh(self):
        # 重建前抓取当前可见树的展开状态（覆盖切换界面/导入/替换等刷新）
        self._save_open_state()
        self.tree.delete(*self.tree.get_children())
        self._expand_map = {}
        mgr = self.app.manager
        if mgr is None:
            self.summary_var.set("未加载皮肤")
            return
        mgr.scan()
        s = mgr.summary()
        self.summary_var.set(f"共 {s['total']} 个元素 | 已有 {s['present']} | 缺失 {s['missing']}")
        flt = self.filter_var.get()
        # 分类显示：开启时按当前预览界面过滤元素；关闭时任意界面都显示全部元素
        if self.app.settings.get("enable_category", True):
            # 根据预览页面的下拉选择筛选元素：仅显示该界面元素 + 通用元素
            page = getattr(self.app.stage_preview, "page_var", None)
            page_name = page.get() if page is not None else "游玩界面"
            if page_name == "游玩界面":
                def screen_match(e):
                    return "游玩" in e.screens or "通用" in e.screens
            else:
                target = PAGE_SCREEN.get(page_name)
                if target is not None:
                    def screen_match(e):
                        return "通用" in e.screens or target in e.screens
                else:
                    screen_match = None
        else:
            screen_match = None
        open_state = self.app.settings.get("element_open_state", {})
        for group, cats in by_group().items():
            group_hits = []
            for cat, elems in cats.items():
                children = []
                for e in elems:
                    if screen_match is not None and not screen_match(e):
                        continue
                    st = mgr.status(e)
                    if flt == "missing" and st.exists:
                        continue
                    if flt == "hd" and (not st.exists or not st.has_hd):
                        continue
                    if flt == "anim" and (not st.exists or not st.frames):
                        continue
                    children.append((e, st))
                if not children:
                    continue
                group_hits.append((cat, children))
            if not group_hits:
                continue
            group_id = self.tree.insert("", "end", text=group,
                                        open=open_state.get(group, True))
            self._expand_map[group_id] = group
            for cat, children in group_hits:
                ckey = f"{group}/{cat}"
                cat_id = self.tree.insert(group_id, "end", text=cat,
                                          open=open_state.get(ckey, True))
                self._expand_map[cat_id] = ckey
                for e, st in children:
                    tags = []
                    if not st.exists:
                        state = "缺失"
                        tags.append("missing")
                    elif st.has_hd:
                        state = "存在(@2x)"
                        tags.append("hd")
                    else:
                        state = "存在"
                        tags.append("ok")
                    if st.frames:
                        state += f" ·{st.frames}帧"
                        tags.append("anim")
                    self.tree.insert(cat_id, "end", iid=e.filename, text=e.filename,
                                     values=(state,), tags=tuple(tags))

    def _save_open_state(self):
        """将当前可见节点（组/分类）的展开状态合并进持久化字典。

        要点：
        - 不使用 self.tree.focus()：点击展开箭头时焦点未必落在该节点，会漏记。
        - 采用“合并而非覆盖”：只更新当前树中存在的节点，保留其它分组此前
          保存的状态。否则切到某个界面时被隐藏分组的折叠状态会被丢弃，且程序
          刚启动第一次 refresh（树为空）会把已持久化状态整体清空。
        """
        st = self.app.settings
        state = dict(st.get("element_open_state", {}))
        changed = False
        for iid, key in self._expand_map.items():
            try:
                val = bool(self.tree.item(iid, "open"))
            except tk.TclError:
                continue
            if state.get(key) != val:
                state[key] = val
                changed = True
        if changed:
            st["element_open_state"] = state
            save_settings(st)

    def _on_open_close(self, event):
        """元素树分类节点展开/收缩时，记录并持久化展开状态。"""
        self._save_open_state()

    def select_element(self, filename):
        """编程选中列表中的指定元素（由游玩预览点击联动触发）。"""
        if not self.tree.exists(filename):
            # 该元素不在当前列表中（被筛选/页面过滤隐藏）：重置为“全部”再刷新
            if self.filter_var.get() != "all":
                self.filter_var.set("all")
                self.refresh()
            page = getattr(self.app.stage_preview, "page_var", None)
            cur = page.get() if page is not None else "游玩界面"
            # 暂停/失败界面固定：点击联动选中时不切回游玩界面（元素由对应页面筛选展示）
            if cur not in ("游玩界面", "暂停界面", "失败界面"):
                page.set("游玩界面")
                self.app.stage_preview._on_page_change()
            if not self.tree.exists(filename):
                return
        self.tree.selection_set(filename)
        self.tree.see(filename)
        self._on_select(None)

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        # 仅对叶子节点（元素）响应，跳过分类节点
        if not self.tree.parent(item):
            return
        e = by_name(item)
        if e is None:
            return
        # 已拥有的元素：在资源管理器中打开所在文件夹并选中对应文件；
        # 缺失的元素：跳到 skin.ini 编辑器的对应字段。
        mgr = self.app.manager
        st = mgr.status(e) if mgr else None
        path = mgr.path_for(e.filename) if (st and st.exists) else None
        if path:
            try:
                subprocess.Popen(["explorer", "/select,", str(path)])
            except Exception:
                os.startfile(os.path.dirname(str(path)))
        else:
            self.app.jump_to_ini_for(item)

    def _on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        e = by_name(sel[0])
        if e is None:
            return
        mgr = self.app.manager
        self._clear_preview()
        self._anim_timer = None  # 停止正在播放的动画
        st = mgr.status(e) if mgr else None
        # 尺寸：优先显示实际图片的像素尺寸；无图时回退到目录建议尺寸
        size_txt = e.size or "-"
        if HAS_PIL and st and st.exists and st.files:
            p = st.files[0]
            try:
                with Image.open(p) as im:
                    w, h = im.size
                hd = " (@2x)" if SkinManager.is_hd_path(p) else ""
                size_txt = f"{w}x{h}px{hd}"
            except Exception:
                pass
        info = f"{e.description}\n尺寸: {size_txt} | 混合: {e.blend} | 原点: {e.origin}"
        if e.animatable:
            info += " | 可动画 -{n}"
        self.info_var.set(info)
        if st and st.exists and HAS_PIL:
            self._show_image(mgr.path_for(e.filename))
            # 操作按钮：用 grid 等权重布局，容器缩小时等比例缩小
            btn_frame = ttk.Frame(self.preview, style="Card.TFrame")
            btn_frame.pack(side="bottom", fill="x", pady=(6, 0))
            btn_frame.columnconfigure(0, weight=1, uniform="btn")
            btn_frame.columnconfigure(1, weight=1, uniform="btn")
            ttk.Button(btn_frame, text="删除素材",
                       command=lambda: self._delete_asset(e.filename, st.files)).grid(
                           row=0, column=0, sticky="ew", padx=(0, 2))
            ttk.Button(btn_frame, text="替换素材",
                       command=lambda: self._replace_asset(e.filename, st.files)).grid(
                           row=0, column=1, sticky="ew", padx=(2, 0))
            # 有动画帧的元素，追加播放按钮
            if st.frames > 0 and st.files:
                self._anim_files = self._collect_frame_files(st.files)
                btn_frame.columnconfigure(2, weight=1, uniform="btn")
                self._anim_btn = ttk.Button(btn_frame, text="播放动画",
                                            command=self._play_animation)
                self._anim_btn.grid(row=0, column=2, sticky="ew", padx=(2, 0))
                self._anim_label = tk.Label(btn_frame, text="",
                                            bg=theme_color("panel"),
                                            fg=theme_color("text_secondary"))
                self._anim_label.grid(row=1, column=0, columnspan=3, sticky="w",
                                      padx=(0, 0), pady=(2, 0))
        elif st and not st.exists and self.app.manager:
            # 缺失素材：显示"添加素材"按钮
            btn_frame = ttk.Frame(self.preview, style="Card.TFrame")
            btn_frame.pack(side="bottom", fill="x", pady=(6, 0))
            ttk.Button(btn_frame, text="添加素材",
                       command=lambda: self._add_asset(e.filename)).pack(fill="x")

    def _collect_frame_files(self, files):
        """从文件列表中收集动画帧，按帧号排序，返回 [(frame, path), ...]。"""
        frames = []
        for p in files:
            _, _, frame = parse_stem(p.stem)
            if frame is not None:
                frames.append((frame, str(p)))
        frames.sort(key=lambda x: x[0])
        return frames

    def _play_animation(self):
        """播放动画：逐帧循环显示。"""
        if not hasattr(self, '_anim_files') or not self._anim_files:
            return
        self._anim_idx = 0
        self._anim_playing = True
        self._anim_btn.configure(text="停止", command=self._stop_animation)
        self._show_anim_frame()

    def _stop_animation(self):
        self._anim_playing = False
        if hasattr(self, '_anim_timer') and self._anim_timer:
            self.after_cancel(self._anim_timer)
            self._anim_timer = None
        if hasattr(self, '_anim_btn'):
            self._anim_btn.configure(text="播放动画", command=self._play_animation)

    def _show_anim_frame(self):
        """显示当前帧，并安排下一帧。"""
        if not self._anim_playing or not hasattr(self, '_anim_files'):
            return
        if self._anim_idx >= len(self._anim_files):
            self._anim_idx = 0
        frame, path = self._anim_files[self._anim_idx]
        # 不销毁重建，直接更新画布图片，避免 pack 顺序导致下移
        self._set_image(path)
        self._anim_label.configure(text=f"第 {frame} 帧")
        self._anim_idx += 1
        self._anim_timer = self.after(100, self._show_anim_frame)

    def _clear_preview(self):
        """清理预览区，保留常驻 Canvas 及其中已设置的视图。"""
        self._preview_label = None
        self._anim_playing = False
        self._img_pil = None
        self._photo = None
        self._canvas_item = None
        self._pan_start = None
        for w in self.preview.winfo_children():
            if getattr(self, '_preview_canvas', None) is w:
                continue
            w.destroy()
        if hasattr(self, '_preview_canvas') and self._preview_canvas.winfo_exists():
            self._preview_canvas.delete("all")

    # -- 可缩放/拖动预览 ---------------------------------------------------
    def _ensure_canvas(self):
        """确保预览 Canvas 存在（常驻，不随选择变化销毁）。"""
        if not hasattr(self, '_preview_canvas') or not self._preview_canvas.winfo_exists():
            self._preview_canvas = tk.Canvas(
                self.preview, bg=theme_color("canvas"), highlightthickness=0)
            self._preview_canvas.pack(side="top", fill="both", expand=True)
            self._preview_canvas.bind("<MouseWheel>", self._on_wheel)
            self._preview_canvas.bind("<Button-4>", self._on_wheel_linux)
            self._preview_canvas.bind("<Button-5>", self._on_wheel_linux)
            self._preview_canvas.bind("<ButtonPress-1>", self._on_pan_start)
            self._preview_canvas.bind("<B1-Motion>", self._on_pan_move)

    def _show_image(self, path):
        """新元素：重置视图并居中显示图片。"""
        self._img_pil = None
        self._zoom = 1.0
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._set_image(path, reset_view=True)

    def _set_image(self, path, reset_view=False):
        """加载图片（处理 @2x 与 1px 放大）并重绘。

        reset_view=True（换元素）时重新居中；动画换帧时保持当前视图。
        """
        try:
            img = Image.open(path).convert("RGBA")
            # @2x 素材按官方规则先缩小为 1x 逻辑尺寸再预览
            if SkinManager.is_hd_path(path):
                w, h = img.size
                img = img.resize((max(1, w // 2), max(1, h // 2)), Image.LANCZOS)
            w, h = img.size
            if w <= 1 or h <= 1:
                # 1 像素图片放大为可见的纯色块，否则几乎看不到
                img = img.resize((64, 64), Image.NEAREST)
            self._ensure_canvas()
            if reset_view or self._img_pil is None:
                self._img_pil = img
                self._canvas_item = None
                self._center_image()
            else:
                self._img_pil = img
            self._redraw()
        except Exception as exc:
            self._img_pil = None
            self._ensure_canvas()
            self._preview_canvas.delete("all")
            self._preview_canvas.create_text(
                self._preview_canvas.winfo_width() // 2,
                self._preview_canvas.winfo_height() // 2,
                text=f"无法预览: {exc}", fill="#a00")

    def _center_image(self):
        """图片居中：缩放至适配画布（小图保持 1:1），默认显示在正中央。"""
        if self._img_pil is None:
            return
        self.preview.update_idletasks()
        cw = max(1, self._preview_canvas.winfo_width())
        ch = max(1, self._preview_canvas.winfo_height())
        w, h = self._img_pil.size
        self._zoom = min(1.0, cw / max(1, w), ch / max(1, h))
        self._offset_x = (cw - w * self._zoom) / 2.0
        self._offset_y = (ch - h * self._zoom) / 2.0

    def _redraw(self):
        """按当前缩放/偏移把图片重绘到画布上。"""
        if self._img_pil is None or not hasattr(self, '_preview_canvas'):
            return
        w, h = self._img_pil.size
        dw = max(1, int(w * self._zoom))
        dh = max(1, int(h * self._zoom))
        img = self._img_pil.resize((dw, dh), Image.LANCZOS)
        self._photo = ImageTk.PhotoImage(img)
        cx = self._offset_x + dw / 2.0
        cy = self._offset_y + dh / 2.0
        if self._canvas_item is None:
            self._canvas_item = self._preview_canvas.create_image(cx, cy, image=self._photo)
        else:
            self._preview_canvas.itemconfigure(self._canvas_item, image=self._photo)
            self._preview_canvas.coords(self._canvas_item, cx, cy)

    def _zoom_at(self, factor, cx, cy):
        """以鼠标位置 (cx, cy) 为中心缩放。"""
        if self._img_pil is None:
            return
        new_zoom = max(0.05, min(self._zoom * factor, 20.0))
        # 缩放前后鼠标下的图像坐标保持不动
        ix = (cx - self._offset_x) / self._zoom
        iy = (cy - self._offset_y) / self._zoom
        self._zoom = new_zoom
        self._offset_x = cx - ix * new_zoom
        self._offset_y = cy - iy * new_zoom
        self._redraw()

    def _on_wheel(self, event):
        self._zoom_at(1.1 if event.delta > 0 else 1 / 1.1, event.x, event.y)

    def _on_wheel_linux(self, event):
        self._zoom_at(1.1 if event.num == 4 else 1 / 1.1, event.x, event.y)

    def _on_pan_start(self, event):
        self._pan_start = (event.x, event.y, self._offset_x, self._offset_y)

    def _on_pan_move(self, event):
        if not self._pan_start:
            return
        sx, sy, ox, oy = self._pan_start
        self._offset_x = ox + (event.x - sx)
        self._offset_y = oy + (event.y - sy)
        self._redraw()

    def _ask_hd(self, filename):
        """按设置决定导入/替换素材时是否添加 @2x 后缀。

        设置项：@2x（直接 @2x）/ 原图（直接原图）/ 自行确认（每次询问）。
        返回 True 表示复制为 元素名@2x.png。
        """
        mode = self.app.import_hd_var.get() if hasattr(self.app, "import_hd_var") else "ask"
        if mode == "hd":
            return True
        if mode == "normal":
            return False
        return messagebox.askyesno(
            "@2x 高清素材",
            f"是否将此素材标记为 @2x（高清）？\n\n"
            f"选择\"是\"：复制为 {filename}@2x.png\n"
            f"选择\"否\"：复制为 {filename}.png"
        )

    def _add_asset(self, filename):
        """为缺失素材打开文件对话框，将选中的图片复制到皮肤根目录并重命名。

        支持选择是否添加 @2x 后缀。对可动画组件支持一次选择多个文件，
        按选择顺序生成动画帧（``名-n`` / ``名-n@2x``）。
        """
        mgr = self.app.manager
        if mgr is None:
            return
        folder = str(mgr.folder)
        e = by_name(filename)
        animatable = bool(e and e.animatable)
        if animatable:
            paths = filedialog.askopenfilenames(
                title=f"选择 {filename} 的动画帧（按播放顺序）",
                initialdir=folder,
                filetypes=[("图片", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")],
            )
        else:
            path = filedialog.askopenfilename(
                title=f"选择 {filename} 的素材图片",
                initialdir=folder,
                filetypes=[("图片", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")],
            )
            paths = (path,) if path else ()
        if not paths:
            return
        # 按设置决定是否添加 @2x 后缀（自行确认模式下询问）
        add_hd = self._ask_hd(filename)
        # 多动画帧：全部用 名-0 起依序编号（裸文件名帧号识别为 None 会被少计帧）；
        # @2x 附加在序号之后（如 名-0@2x）
        multi = animatable and len(paths) > 1
        for idx, path in enumerate(paths):
            ext = os.path.splitext(path)[1].lower() or ".png"
            base = filename if not multi else f"{filename}-{idx}"
            suffix = "@2x" if add_hd else ""
            dest_name = f"{base}{suffix}{ext}"
            dest = os.path.join(folder, dest_name)
            if os.path.exists(dest):
                if not messagebox.askyesno(
                    "覆盖确认", f"文件 {dest_name} 已存在，是否覆盖？"):
                    return
            try:
                shutil.copy2(path, dest)
            except Exception as exc:
                messagebox.showerror("复制失败", f"无法复制文件：{exc}")
                return
        self._post_modify(filename)

    def _delete_asset(self, filename, files):
        """删除该元素的所有素材文件，确认后执行。"""
        if not files:
            return
        names = "\n".join(f"  - {os.path.basename(p)}" for p in files)
        if not messagebox.askyesno("删除确认", f"确定删除以下素材文件？\n\n{names}"):
            return
        for p in files:
            try:
                os.remove(p)
            except Exception as exc:
                messagebox.showerror("删除失败", f"无法删除 {os.path.basename(p)}：{exc}")
                return
        self._post_modify(filename)

    def _replace_asset(self, filename, files):
        """删除旧素材并用新选择的文件替换，新文件复制到根目录并以元素名命名。

        对可动画组件支持一次选择多个文件，按选择顺序生成动画帧
        （``名-n`` / ``名-n@2x``）。
        """
        mgr = self.app.manager
        if mgr is None:
            return
        folder = str(mgr.folder)
        e = by_name(filename)
        animatable = bool(e and e.animatable)
        if animatable:
            paths = filedialog.askopenfilenames(
                title=f"选择替换 {filename} 的动画帧（按播放顺序）",
                initialdir=folder,
                filetypes=[("图片", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")],
            )
        else:
            path = filedialog.askopenfilename(
                title=f"选择替换 {filename} 的素材图片",
                initialdir=folder,
                filetypes=[("图片", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")],
            )
            paths = (path,) if path else ()
        if not paths:
            return
        # 按设置决定是否添加 @2x 后缀（自行确认模式下询问）
        add_hd = self._ask_hd(filename)
        # 多动画帧：全部用 名-0 起依序编号（裸文件名帧号识别为 None 会被少计帧）；
        # @2x 附加在序号之后（如 名-0@2x）
        multi = animatable and len(paths) > 1
        dests = []
        for idx, path in enumerate(paths):
            ext = os.path.splitext(path)[1].lower() or ".png"
            base = filename if not multi else f"{filename}-{idx}"
            suffix = "@2x" if add_hd else ""
            dest_name = f"{base}{suffix}{ext}"
            dest = os.path.join(folder, dest_name)
            if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(dest)):
                # 用户选择的源就是目标文件本身：无需复制（否则复制会覆盖自己），
                # 记录为本次目标供删除阶段跳过，避免源先被删除、复制又失败而凭空消失
                dests.append(dest)
                continue
            try:
                shutil.copy2(path, dest)
            except Exception as exc:
                messagebox.showerror("复制失败", f"无法复制文件：{exc}")
                return
            dests.append(dest)
        # 先复制、后删除；删除旧文件时跳过本次写出/保留的目标，防止误删源文件
        dest_set = set(os.path.normcase(os.path.abspath(d)) for d in dests)
        for p in files:
            if os.path.normcase(os.path.abspath(p)) in dest_set:
                continue
            try:
                os.remove(p)
            except Exception:
                pass  # 删除失败不影响其它文件
        self._post_modify(filename)

    def _post_modify(self, filename):
        """删除/替换/添加后的统一刷新逻辑。"""
        mgr = self.app.manager
        if mgr is None:
            return
        mgr.scan()
        self.refresh()
        self.app.stage_preview.refresh()
        self.app.mania_editor.refresh()
        self.tree.selection_set(filename)
        self.tree.see(filename)
        self._on_select(None)


# ---------------------------------------------------------------------------
# 游玩预览（mania 舞台示意）
# ---------------------------------------------------------------------------

NOTE_COLORS = ["#4fc3f7", "#ff8a65", "#fff176", "#aed581", "#f06292",
               "#ba68c8", "#4db6ac", "#ffd54f", "#90a4ae"]

# 数字/标点字符 -> 皮肤文件名后缀（前缀来自 [Fonts] ScorePrefix / ComboPrefix）
_DIGIT_FILES = {
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    ",": "comma", ".": "dot", "%": "percent", "x": "x",
}


class StagePreview(ttk.Frame):
    """根据 skin.ini 的 [Mania] 设置绘制游玩舞台示意（16:9 / 16:10 可选）。

    参考坐标系：游戏区域高度固定为 480 单位，宽度随画面比例变化
    （宽度 = 480 ÷ 高 × 宽）；面板以 ColumnStart 从左侧绝对定位，
    因此 mania 演奏面板整体偏左。
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._img_cache = {}       # path -> PIL.Image（跨刷新复用）
        self._photo_cache = {}     # (path, int(w), int(h)) -> PhotoImage
        self._hold_body_cache = {} # 长条 body 合成图缓存：合成参数 -> PIL.Image
        self._digit_path_cache = {}  # (prefix, ch) -> 数字皮肤图路径（换肤时随 clear_img_cache 清除）
        self._refresh_timer = None  # 防抖定时器 ID
        self.aspect_var = tk.StringVar(value="16:9")
        self.bg_var = tk.BooleanVar(value=True)   # 是否显示皮肤背景（menu-bg）
        self.cb_var = tk.BooleanVar(value=True)   # 是否显示连击图（comboburst）
        self.warning_var = tk.BooleanVar(value=True)  # 是否显示警告箭头（warningarrow）
        self.skip_var = tk.BooleanVar(value=True)  # 是否显示跳过按钮（play-skip）
        # 可自定义的预览数值
        self.score_text_var = tk.StringVar(value="12345678")
        self.acc_text_var = tk.StringVar(value="98.76%")
        self.combo_text_var = tk.StringVar(value="1234")
        self.hit_text_var = tk.StringVar(value="300")
        self._build()
        self._restore_preview_settings()

    def _restore_preview_settings(self):
        """从 settings.json 恢复上次预览状态：页面类型、显示开关、比例与数值。"""
        s = getattr(self.app, "settings", None) or {}
        page = s.get("preview_page", "游玩界面")
        if page in ("游玩界面", "暂停界面", "失败界面", "成绩结算界面", "选歌界面"):
            self.page_var.set(page)
        self.bg_var.set(bool(s.get("preview_bg", True)))
        self.cb_var.set(bool(s.get("preview_cb", True)))
        self.warning_var.set(bool(s.get("preview_warning", True)))
        self.skip_var.set(bool(s.get("preview_skip", True)))
        if s.get("preview_aspect") in ("16:9", "16:10"):
            self.aspect_var.set(s["preview_aspect"])
        for key, var, dft in (("preview_score", self.score_text_var, "12345678"),
                              ("preview_acc", self.acc_text_var, "98.76%"),
                              ("preview_combo", self.combo_text_var, "1234"),
                              ("preview_hit", self.hit_text_var, "300")):
            v = s.get(key, dft)
            if isinstance(v, str):
                var.set(v)

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=(8, 6))

        # 页面选择下拉（预览界面上方）。当前仅提供入口，各页面展示
        # （暂停/失败/结算/选歌）后续实现，选中后暂不切换画面。
        self.page_var = tk.StringVar(value="游玩界面")
        self.page_combo = ttk.Combobox(
            top, textvariable=self.page_var, state="readonly", width=12,
            values=("游玩界面", "暂停界面", "失败界面",
                    "成绩结算界面", "选歌界面"))
        self.page_combo.pack(side="left")
        self.page_combo.bind("<<ComboboxSelected>>", self._on_page_change)

        # 比例
        ttk.Label(top, text="比例:").pack(side="left", padx=(14, 2))
        for a in ("16:9", "16:10"):
            ttk.Radiobutton(top, text=a, value=a, variable=self.aspect_var,
                            command=self.refresh).pack(side="left", padx=2)

        # 开关（背景/连击图/警告箭头）
        ttk.Button(top, text="显示", command=self._open_show_dialog,
                   style="Tool.TButton").pack(side="left", padx=(10, 4))

        # 自定义数值
        ttk.Button(top, text="数值", command=self._open_value_dialog,
                   style="Tool.TButton").pack(side="left", padx=(6, 0))

        self.info_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.info_var,
                  style="Secondary.TLabel").pack(side="left", padx=12)
        ttk.Button(top, text="刷新", command=self.refresh,
                   style="Tool.TButton").pack(side="right")

        self.canvas = tk.Canvas(self, bg="#0b0b0e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.canvas.bind("<Configure>", lambda e: self.refresh())
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Double-1>", self._on_canvas_double_click)

    def _pick_items(self, x, y):
        """返回点击位置命中的带 pick: 标签的画布项（按创建顺序：底层→顶层）。"""
        return [it for it in self.canvas.find_overlapping(x, y, x, y)
                if any(t.startswith("pick:") for t in self.canvas.gettags(it))]

    def _pick_select(self, item):
        """把画布项对应的皮肤元素联动到元素管理面板。"""
        for t in self.canvas.gettags(item):
            if t.startswith("pick:"):
                self.app.select_element(t[5:])
                return True
        return False

    def _on_canvas_click(self, event):
        """单击：联动选中点击位置最顶层的组件。

        同时记录命中栈，供双击逐层向下选中被上层遮挡的组件。
        """
        if not self.app.click_select_var.get():
            return
        pick = self._pick_items(event.x, event.y)
        if not pick:
            return
        self._pick_stack = pick          # 底层→顶层
        self._pick_idx = len(pick) - 1   # 当前选中层（最顶层）
        self._pick_select(pick[-1])

    def _on_canvas_double_click(self, event):
        """双击：选中点击位置被最上层遮挡的下一层组件。

        在单击命中的同一组组件中向更底层移动一层；再次双击继续深入，
        到底层后循环回顶层。
        """
        if not self.app.click_select_var.get():
            return
        pick = self._pick_items(event.x, event.y)
        if not pick:
            return
        # 同一位置且命中集合与上次单击一致：从当前层向下一层移动
        if (getattr(self, "_pick_stack", None) == pick
                and getattr(self, "_pick_idx", None) is not None):
            idx = (self._pick_idx - 1) % len(pick)
        else:
            idx = len(pick) - 2 if len(pick) > 1 else 0
        self._pick_stack = pick
        self._pick_idx = idx
        self._pick_select(pick[idx])

    def _on_page_change(self, _event=None):
        """页面下拉切换：重绘预览画面，并同步元素管理面板的筛选。"""
        self.refresh()
        ep = getattr(self.app, "element_panel", None)
        if ep is not None:
            ep.refresh()

    # 判定评分可选值（对应皮肤 hitburst 命名，见 catalog 的“打击判定”分类）
    HIT_CHOICES = ["300g", "300", "200", "100", "50", "miss"]

    # 判定评分值 -> 依次尝试的皮肤文件名（mania-* 优先，其次旧式 hit*）
    HIT_LOOKUP = {
        "300g": ["mania-hit300g", "hit300g"],
        "300": ["mania-hit300", "hit300"],
        "200": ["mania-hit200", "hit200"],
        "100": ["mania-hit100", "hit100"],
        "50": ["mania-hit50", "hit50"],
        "miss": ["mania-hit0", "hit0"],
    }

    # 判定评分值 -> skin.ini 中对应的 [Mania] 命令名
    HIT_INI_KEYS = {
        "300g": "Hit300g",
        "300":  "Hit300",
        "200":  "Hit200",
        "100":  "Hit100",
        "50":   "Hit50",
        "miss": "Hit0",
    }

    def _open_show_dialog(self):
        """弹出小弹窗，勾选游玩预览中是否显示背景图/连击图/警告箭头。"""
        dlg = tk.Toplevel(self)
        dlg.title("预览显示开关")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=theme_color("bg"))
        rows = (
            ("显示背景图（menu-background）", self.bg_var),
            ("显示连击图（comboburst）", self.cb_var),
            ("显示警告箭头（mania-warningarrow）", self.warning_var),
            ("显示跳过按钮（play-skip）", self.skip_var),
        )
        for i, (text, var) in enumerate(rows):
            ttk.Checkbutton(dlg, text=text, variable=var,
                            command=self.refresh).grid(
                                row=i, column=0, sticky="w", padx=10, pady=5)
        ttk.Button(dlg, text="关闭", command=dlg.destroy).grid(
            row=len(rows), column=0, pady=(2, 8))
        self.after(50, lambda: dlg.geometry(f"+{self.winfo_rootx()+80}+{self.winfo_rooty()+80}"))

    def _open_value_dialog(self):
        """弹出对话框，自定义预览中显示的分数/acc/连击/评分。"""
        dlg = tk.Toplevel(self)
        dlg.title("自定义预览数值")
        dlg.transient(self)
        dlg.grab_set()
        dlg.configure(bg=theme_color("bg"))
        ttk.Label(dlg, text="分数:").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dlg, textvariable=self.score_text_var, width=16).grid(row=0, column=1, padx=8, pady=4)
        ttk.Label(dlg, text="准确度:").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dlg, textvariable=self.acc_text_var, width=16).grid(row=1, column=1, padx=8, pady=4)
        ttk.Label(dlg, text="连击数:").grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(dlg, textvariable=self.combo_text_var, width=16).grid(row=2, column=1, padx=8, pady=4)
        ttk.Label(dlg, text="中间评分:").grid(row=3, column=0, sticky="w", padx=8, pady=4)
        ttk.Combobox(dlg, textvariable=self.hit_text_var, values=self.HIT_CHOICES,
                     state="readonly", width=14).grid(row=3, column=1, padx=8, pady=4)

        def _ok():
            dlg.destroy()
            self.refresh()

        ttk.Button(dlg, text="确定", command=_ok).grid(row=4, column=0, columnspan=2, pady=10)
        self.after(50, lambda: dlg.geometry(f"+{self.winfo_rootx()+80}+{self.winfo_rooty()+80}"))

    def refresh(self):
        """防抖刷新：取消上次定时，延迟 200ms 后执行实际绘制。"""
        if self._refresh_timer is not None:
            self.after_cancel(self._refresh_timer)
        self._refresh_timer = self.after(200, self._do_refresh)

    def _do_refresh(self):
        self._refresh_timer = None
        self.canvas.delete("all")
        # 注意：不清 _img_cache / _photo_cache——PIL 原图与 PhotoImage 均跨刷新复用
        # （_photo 以 (img, w, h, flip) 为键缓存），避免每次改动字段都全量重建贴图导致卡顿。
        # 换肤时会经 clear_img_cache 统一清空。
        if self.app.manager is None:
            self.canvas.create_text(self.canvas.winfo_width() // 2, 40,
                                    text="请先打开皮肤文件夹", fill="#999")
            return
        # 重新扫描皮肤文件夹：识别外部新增/删除/覆盖的素材文件
        if self.app.skin_folder and os.path.isdir(self.app.skin_folder):
            self.app.manager.scan()
        vals = self._collect_values()
        self._draw(vals)

    def _collect_values(self):
        ed = self.app.mania_editor
        vals = {k: v.get() for k, v in ed.all_vars.items()}
        vals["Keys"] = ed.keys_var.get()
        return vals

    def _parse_rgba(self, text, default=(0, 0, 0, 255)):
        parts = [p.strip() for p in str(text).split(",")] if text else []
        if len(parts) < 3:
            return default
        rgb = [_num(parts[0], default[0]), _num(parts[1], default[1]), _num(parts[2], default[2])]
        a = _num(parts[3], default[3]) if len(parts) >= 4 else default[3]
        return (int(max(0, min(255, rgb[0]))), int(max(0, min(255, rgb[1]))),
                int(max(0, min(255, rgb[2]))), int(max(0, min(255, a))))

    def _mgr_path(self, base, exact=False):
        """按 base 查 SkinManager 的文件路径；exact=True 时仅精确匹配
        （skin.ini 指定的路径不应回退到根目录同名文件）。"""
        mgr = self.app.manager
        if not mgr or not base:
            return None
        return mgr.path_for_exact(base) if exact else mgr.path_for(base)

    def _show_default_on(self) -> bool:
        """“缺失组件显示默认组件”设置开关是否开启（默认组件保持原样）。"""
        v = getattr(self.app, "show_default_var", None)
        return bool(v is not None and v.get())

    def _img_path(self, base):
        return self._mgr_path(base)

    def _img_path_exact(self, base):
        return self._mgr_path(base, exact=True)

    def _resolve_path(self, ini_value, *default_bases):
        """按官方优先级解析素材路径，返回文件路径或 None。

        优先级（与 osu! 官方行为一致）：
        1. skin.ini 指定的路径 → @2x 版本
        2. skin.ini 指定的路径 → 原版（非 @2x）
        3. 默认文件名 → @2x 版本（从根目录/子目录查找）
        4. 默认文件名 → 原版（从根目录/子目录查找）

        返回第一个能命中的文件路径；全部找不到返回 None。
        """
        # 优先：skin.ini 指定路径（精确匹配，@2x 优先）
        if ini_value:
            probe = ini_value.strip().strip('"')
            # skin.ini 路径可带图片扩展名（如 mania/key-60-white.png），而扫描索引
            # 用 parse_stem 去掉了扩展名；这里剥离后再匹配，带不带后缀都能命中
            if os.path.splitext(probe)[1].lower() in (".png", ".gif", ".jpg", ".jpeg"):
                probe = os.path.splitext(probe)[0]
            p = self._img_path_exact(probe)
            if p:
                return p
        # 其次：默认文件名（模糊匹配，@2x 优先，支持回退到 stem 查找）
        for base in default_bases:
            if base:
                p = self._img_path(base)
                if p:
                    return p
        return None

    def _open_img_or_none(self, path):
        """统一入口：返回已处理 @2x 的 PIL 图，不可用时返回 None。"""
        if not HAS_PIL or path is None:
            return None
        return self._open_skin_image(path)

    def _open_skin_image(self, path):
        """打开皮肤图片并按官方规则处理 @2x（带缓存，跨刷新复用）。

        缓存记录文件修改时间与大小：素材文件被覆盖/替换后（mtime 或大小
        变化）下次绘制会自动重新加载，无需手动清缓存。
        """
        if not HAS_PIL or path is None:
            return None
        try:
            st = os.stat(path)
            mtime, size = st.st_mtime, st.st_size
        except OSError:
            return None
        ent = self._img_cache.get(path)
        if ent is not None and ent[0] == mtime and ent[1] == size:
            return ent[2]
        try:
            img = Image.open(path).convert("RGBA")
            if img.size[0] <= 0 or img.size[1] <= 0:
                img = Image.new("RGBA", (1, 1))
            if SkinManager.is_hd_path(path):
                w, h = img.size
                w, h = max(1, w // 2), max(1, h // 2)
                img = img.resize((w, h), Image.LANCZOS)
            self._img_cache[path] = (mtime, size, img)
            img._skin_key = path        # 稳定键：供 _photo 缓存使用，避免 id 复用误命中
            img._skin_mtime = mtime     # 内容标识：_photo 缓存键加入 mtime，防同路径换图仍显示旧图
            return img
        except Exception:
            return None

    def clear_img_cache(self):
        """换肤时清除 PIL 原图缓存与 PhotoImage 缓存。

        canvas 上仍引用着旧 PhotoImage，但 delete("all") 之后它们不再被画布
        引用，若缓存已清空会被 GC 导致画面闪空；所以应由下一次 _do_refresh
        在 delete("all") 之后重绘时按需重建。跨皮肤不留旧图可防止内存累积。
        """
        self._img_cache.clear()
        self._photo_cache.clear()
        self._hold_body_cache.clear()
        self._digit_path_cache.clear()

    def _photo(self, img, w, h, flip_h=False, flip_v=False):
        """把 PIL.Image 缩放到 w×h 并转成 PhotoImage（带缓存，保存引用防 GC）。
        翻转在缩放后进行（垂直/水平翻转与缩放可交换），与缩放共用同一缓存条目。"""
        # 缓存键优先用 img 绑定的稳定键（_open_skin_image 设置），
        # 避免用 id(img)：临时构造的合成图（如 body 平铺）每次 id 都变，
        # 导致缓存永不命中；同时避免对象被 GC 后 id 复用造成误命中。
        # 键中并入 _skin_mtime：同一路径文件被替换（内容变化）后不再命中
        # 旧 PhotoImage，否则“删除素材后重新添加”会一直显示旧图。
        key = (getattr(img, "_skin_key", None) or id(img),
               getattr(img, "_skin_mtime", None),
               int(w), int(h), bool(flip_h), bool(flip_v))
        if key in self._photo_cache:
            return self._photo_cache[key]
        img = img.resize((max(1, int(w)), max(1, int(h))), Image.LANCZOS)
        if flip_v:
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        if flip_h:
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        photo = ImageTk.PhotoImage(img)
        self._photo_cache[key] = photo
        return photo

    def _tint(self, img, rgb):
        """把图片与一个纯色相乘（对应 osu! 的 Multiplicative 混合）。
        rgb 为 (r,g,b) 0-255；返回新的 RGBA 图。"""
        tint = Image.new("RGBA", img.size, (int(rgb[0]), int(rgb[1]), int(rgb[2]), 255))
        return ImageChops.multiply(img.convert("RGBA"), tint)

    def _build_hold_body(self, body_path, note_body_style, body_w, target_h,
                         note_ref_w, scale, hold_rgba):
        """合成长条 body 图（带缓存，跨刷新复用），返回 (合成图, 源图宽度)。

        合成是每帧最重的 PIL 操作（resize/裁剪/平铺/着色），且结果只依赖
        有限的输入参数，故按 (路径, mtime, 样式, 尺寸, 颜色) 缓存；素材被
        覆盖（mtime 变）或换肤时自动失效，无需手动清理。
        """
        try:
            mtime = os.path.getmtime(body_path)
        except OSError:
            mtime = 0
        key = (body_path, mtime, note_body_style, int(body_w), int(target_h),
               tuple(hold_rgba[:3]))
        hit = self._hold_body_cache.get(key)
        if hit is not None:
            return hit
        img = self._open_img_or_none(body_path)
        if img is None:
            return None, 0
        iw, ih = img.size
        if iw <= 0 or ih <= 0:
            return None, 0
        k = note_ref_w / iw                 # 公共缩放比
        tile_h = ih * k * scale             # 单张 body 等比后的高度（像素）
        if note_body_style == 0:
            # 拉伸样式：单张图直接拉伸填满（不保持宽高比）
            body_img = img.resize((max(1, int(body_w)), max(1, int(target_h))),
                                  Image.LANCZOS)
        elif tile_h >= target_h:
            # 单张足够：按样式取向一侧裁剪（避免处理超长图）——
            # 从顶取源图顶部，从底取源图底部
            src_h = int(target_h / k) if k > 0 else 1
            src_h = max(1, min(src_h, ih))
            if note_body_style == 2:
                body_img = img.crop((0, ih - src_h, iw, ih))
            else:
                body_img = img.crop((0, 0, iw, src_h))
            body_img = body_img.resize((max(1, int(body_w)), max(1, int(target_h))),
                                       Image.LANCZOS)
        else:
            # 单张不够：等比缩放单张后平铺到所需高度
            tile = img.resize((max(1, int(body_w)), max(1, int(tile_h))),
                              Image.LANCZOS)
            body_img = Image.new("RGBA", (max(1, int(body_w)), max(1, int(target_h))),
                                 (0, 0, 0, 0))
            step = max(1, int(tile_h))
            if note_body_style == 2:
                # 从底：最后一片完整贴底端（头图中心），自底向上平铺，
                # 顶端不足一张的部分由画布自动截断，不留透明空隙
                for y in range(int(target_h) - step, -step, -step):
                    body_img.paste(tile, (0, y))
            else:
                # 从顶：自顶部向下平铺（超出部分自动截断）
                for y in range(0, int(target_h), step):
                    body_img.paste(tile, (0, y))
        # ColourHold 覆盖长条身体颜色（默认白色 = 不变，跳过乘算避免重建）
        if hold_rgba[:3] != (255, 255, 255):
            body_img = self._tint(body_img, hold_rgba[:3])
        self._hold_body_cache[key] = (body_img, iw)
        return body_img, iw

    def _load_photo_fit_height(self, path, target_h, flip_v=False, flip_h=False):
        """按目标高度等比缩放（基于 1x 逻辑尺寸），返回 (photo, width)。"""
        img = self._open_img_or_none(path)
        if img is None:
            return None, 0
        w, h = img.size
        if h <= 0:
            return None, 0
        try:
            tw = max(1, int(w * target_h / h))
            return self._photo(img, tw, target_h, flip_v=flip_v, flip_h=flip_h), tw
        except Exception:
            return None, 0

    def _load_photo_fit_width(self, path, target_w, flip_v=False):
        """按目标宽度等比缩放（基于 1x 逻辑尺寸），返回 (photo, height)。"""
        img = self._open_img_or_none(path)
        if img is None:
            return None, 0
        w, h = img.size
        if w <= 0:
            return None, 0
        try:
            th = max(1, int(h * target_w / w))
            return self._photo(img, target_w, th, flip_v=flip_v), th
        except Exception:
            return None, 0

    def _load_photo_stretch_width(self, path, target_w, scale, flip_v=False):
        """接收器专用：只按轨道宽度拉伸（高度不变）。
        官方规则（KeyImage）：
        - 宽度强制拉伸到列宽 target_w（屏幕像素）
        - 高度保持图片原始高度，但图片 1 物理像素 = 1/1.6 场地单位
          （SD 理想宽度 = ColumnWidth × 1.6），因此显示高度 =
          图片 1x 逻辑高度 / 1.6 × scale。@2x 已在 _open_skin_image 中减半。
        返回 (photo, 显示高度屏幕像素)。
        """
        img = self._open_img_or_none(path)
        if img is None:
            return None, 0
        w, h = img.size
        try:
            target_h = max(1, int(h * scale / 1.6))
            return self._photo(img, target_w, target_h, flip_v=flip_v), target_h
        except Exception:
            return None, 0

    def _load_photo_natural(self, path, scale, flip_v=False):
        """按图片 1x 逻辑尺寸显示（仅乘画布 scale），不拉伸、不裁剪。

        mania-stage-bottom 按官方规则以 480px 舞台高为基准设计（skinned for a
        480px playfield height），1 逻辑像素 = 1 场地单位，无需 ÷1.6。
        返回 (photo, 宽, 高)。
        """
        img = self._open_img_or_none(path)
        if img is None:
            return None, 0, 0
        w, h = img.size
        try:
            return (self._photo(img, w * scale, h * scale, flip_v=flip_v),
                    max(1, int(w * scale)), max(1, int(h * scale)))
        except Exception:
            return None, 0, 0

    def _draw_stage_side(self, path, edge_x, top_y, full_h, align_right, tag=None):
        """绘制舞台左右边框：垂直拉伸到舞台全高，宽度保持图片逻辑宽度。

        官方规则（Skinning/osu!mania）：
        “This element is stretched to fit the stage height (allows for shorter
        images).”——高度直接拉伸到舞台高度，不做等比缩放（宽高比不保持）。
        图片基准为 x768（Max height 768px），宽度换算到 x480 预览坐标系需 ÷1.6；
        @2x 已在 _open_skin_image 中减半为 1x 逻辑尺寸。
        注意：左右舞台在 UpsideDown（倒置）时不随舞台翻转，图像保持正立。
        """
        img = self._open_img_or_none(path)
        if img is not None and img.size[1] > 0:
            iw = img.size[0]
            scale = full_h / 480.0
            disp_w = max(1, int(iw / 1.6 * scale))
            photo = self._photo(img, disp_w, full_h)
            x = edge_x - disp_w if align_right else edge_x
            self.canvas.create_image(x, top_y, image=photo, anchor="nw",
                                     tags=(f"pick:{tag}",) if tag else ())
            return
        # 兜底：缺失舞台时按“是否显示默认组件”决定——不显示则跳过；显示则用默认灰色占位
        if not self._show_default_on():
            return
        w = max(2, full_h * 0.018)  # 舞台左右占位适度收细
        x0 = edge_x - w if align_right else edge_x
        x1 = edge_x if align_right else edge_x + w
        self.canvas.create_rectangle(x0, top_y, x1, top_y + full_h,
                                     fill="#3a3a44", outline="")

    def _draw_stage_bottom(self, path, center_x, bottom_y, scale, upside=False, tag=None):
        """绘制舞台底部（mania-stage-bottom）。

        官方规则（Skinning/osu!mania）：
        - 不拉伸：大小完全由图片像素尺寸决定（仅乘画布 scale）；
          以 480px 舞台高为基准设计，1 逻辑像素 = 1 场地单位（无需 ÷1.6）
        - 锚点：Bottom —— 图片底部中心固定在演奏面板底部中心
        - 图层：覆盖整个舞台（包括按键和音符），但位于 HUD 之下
        - 倒置时：位置移到舞台顶部（由调用方用 Y(480) 换算），锚点改 N 从顶向下
          悬挂，图像内容不翻转
        """
        if path:
            photo, tw, th = self._load_photo_natural(path, scale)
            if photo:
                self.canvas.create_image(center_x, bottom_y, image=photo,
                                         anchor="n" if upside else "s",
                                         tags=(f"pick:{tag}",) if tag else ())
                return
        # 兜底：缺失舞台底时按“是否显示默认组件”决定——不显示则跳过；显示则用默认灰色占位
        if not self._show_default_on():
            return
        w = max(10, int(120 * scale))
        h = max(10, int(48 * scale))
        self.canvas.create_rectangle(center_x - w / 2, bottom_y - h,
                                     center_x + w / 2, bottom_y,
                                     fill="#3a3a44", outline="")

    def _digit_path(self, prefix, ch):
        """返回字符对应的数字/标点皮肤图片路径，找不到返回 None（带缓存）。"""
        name = _DIGIT_FILES.get(ch)
        mgr = self.app.manager
        if not name or mgr is None:
            return None
        key = (prefix, ch)
        hit = self._digit_path_cache.get(key)
        if hit is not None:
            return hit
        path = mgr.path_for_stem(f"{prefix}-{name}")
        self._digit_path_cache[key] = path
        return path

    def _draw_number(self, text, prefix, cx, cy, anchor, digit_h, overlap=0, tag=None):
        """用皮肤数字图渲染一串字符，缺失时回退为文字。

        cy 为数字顶部；anchor 取 'left' / 'center' / 'right'（cx 对应左/中/右边界）。
        overlap 为数字之间的重叠量（像素）：>0 拉近、<0 分开，对应 [Fonts] 的
        ScoreOverlap/ComboOverlap（lazer 中 Spacing = -Overlap，即步长 = 字宽 - Overlap），
        已换算到预览画布（÷1.6 再乘画布 scale）。
        tag：为该串数字的画布项打 pick:<tag> 标签（点击联动选中用）。
        """
        items = []
        for ch in text:
            path = self._digit_path(prefix, ch)
            photo = None
            w = 0
            if path:
                photo, w = self._load_photo_fit_height(path, digit_h)
            if photo is None:
                w = max(int(digit_h * 0.6), 1)
            items.append((ch, photo, w))
        n = len(items)
        total_w = sum(it[2] for it in items) - overlap * (n - 1)
        if anchor == "center":
            x = cx - total_w / 2
        elif anchor == "right":
            x = cx - total_w
        else:
            x = cx
        for ch, photo, w in items:
            if photo is not None:
                self.canvas.create_image(x, cy, image=photo, anchor="nw",
                                         tags=(f"pick:{tag}",) if tag else ())
            else:
                self.canvas.create_text(x + w / 2, cy + digit_h / 2, text=ch,
                                        fill="#ffffff",
                                        font=("Microsoft YaHei UI",
                                              max(int(digit_h * 0.8), 8), "bold"))
            x += w - overlap
        return total_w

    def _draw_scorebar(self, right_x, bottom_y, scale):
        """绘制 osu!mania 血条（引擎硬编码规则）。

        变换规则（bg 与 colour 作为整体）：
        - scorebar-colour 相对 scorebar-bg 左上角带初始锚点偏移：
            scorebar-marker.png 存在      -> (12, 12)（最高优先级）
            否则（含仅有 ki/kidanger 等） -> (5, 16)（默认行为）
        - 逆时针旋转 90°，再缩放至原始大小的 0.7 倍
        - 变换原点 = bg 左上角（旋转后位于血条左下角），
          锚定在最右轨道右侧、贴场地底边
        - 血量从底部向上填充（底部 = 满血）；预览固定以满血显示，
          避免 crop 切断 colour 右侧内容（旋转后为上方）

        注意：@2x 图片已在 _open_skin_image 中减半为 1x 逻辑尺寸，
        因此锚点偏移沿用 1x 数值（等价于官方在 @2x 上偏移量翻倍）。

        另外，血条是 HUD（屏幕）级元素，官方在 x768 基准坐标系中变换，
        预览画布是 x480 坐标系，因此最终尺寸还需 ÷1.6
        （STABLE_MAGIC_SCALE_FACTOR，与连击/判定评分一致）。
        """
        hp = 1.0          # 满血显示，完整呈现 colour 图片
        shrink = 0.7
        pos_scale = 1.6   # x768 / x480 换算因子

        # 1) 锚点偏移：marker 最高优先级；否则一律 (5, 16)
        off_x, off_y = (12, 12) if self._img_path("scorebar-marker") else (5, 16)

        # 2) 打开横向原图（已按 @2x 规则减半为 1x 逻辑尺寸）
        bg_img = self._open_skin_image(self._img_path("scorebar-bg"))
        colour_img = self._open_skin_image(self._img_path("scorebar-colour"))

        if bg_img is None and colour_img is None:
            if not HAS_PIL:
                return
            # 兜底：示意竖条（按 0.7 缩放、x768→x480 换算后的粗略尺寸）
            w = max(6, int(12 * scale * shrink / pos_scale))
            h = max(1, int(480 * scale * shrink / pos_scale))
            self.canvas.create_rectangle(right_x, bottom_y - h,
                                         right_x + w, bottom_y,
                                         fill="#20202a", outline="#4a4a55")
            return

        # 3) 组合图层：bg 左上角为原点 (0,0)，colour 带锚点偏移叠加；
        #    满血时保留整张 colour（lazer 中 LegacyFill 为 Masking=true，
        #    血量变化时裁切右端，但预览固定满血，故不裁切）
        if bg_img is not None:
            bg_w, bg_h = bg_img.size
        else:
            bg_w, bg_h = 757, 72          # 社区常见 1x 尺寸，仅作兜底参考

        cw, ch = bg_w, bg_h
        if colour_img is not None:
            col_w, col_h = colour_img.size
            cw = max(cw, off_x + col_w)
            ch = max(ch, off_y + col_h)
        combo = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        if bg_img is not None:
            combo.paste(bg_img, (0, 0), bg_img)
        if colour_img is not None:
            keep_w = max(1, int(col_w * hp))
            part = colour_img.crop((0, 0, keep_w, col_h))
            combo.paste(part, (off_x, off_y), part)
        else:
            # 无 colour 图片：以半透明绿色示意血量
            fill_w = max(1, int((cw - off_x) * hp))
            fill_h = max(1, ch - off_y)
            green = Image.new("RGBA", (fill_w, fill_h), (76, 175, 80, 190))
            combo.paste(green, (off_x, off_y), green)

        # 4) 整体变换：逆时针旋转 90° + 缩放 0.7 + x768→x480 换算（再乘画布 scale）
        img = combo.transpose(Image.Transpose.ROTATE_90)
        out_w = max(1, int(img.size[0] * shrink / pos_scale * scale))
        out_h = max(1, int(img.size[1] * shrink / pos_scale * scale))
        photo = self._photo(img, out_w, out_h)

        # 5) 定位：变换原点（bg 左上角，旋转后位于血条左下角）
        #    锚定在最右轨道右侧、贴场地底边，血条向右上方延伸
        self.canvas.create_image(right_x, bottom_y, image=photo, anchor="sw",
                                 tags=("pick:scorebar-colour",))

        # 6) 血量标记（scorebar-marker）：同样旋转缩放后放在填充末端
        marker_path = self._img_path("scorebar-marker")
        if marker_path:
            marker_img = self._open_skin_image(marker_path)
            if marker_img is not None:
                m = marker_img.transpose(Image.Transpose.ROTATE_90)
                mw = max(1, int(m.size[0] * shrink / pos_scale * scale))
                mh = max(1, int(m.size[1] * shrink / pos_scale * scale))
                mphoto = self._photo(m, mw, mh)
                fill_h = max(1, int(out_h * hp))
                self.canvas.create_image(right_x + out_w / 2, bottom_y - fill_h,
                                         image=mphoto, anchor="center",
                                         tags=("pick:scorebar-marker",))

    # 暂停界面按钮（官方 SDK 基准：x768 满高 768，与 pause-overlay 背景同一参考系；
    # 按钮纵坐标 224 / 400 / 576 为 SD 高度，预览换算 ÷1.6）
    PAUSE_BUTTONS = (
        ("pause-continue", "继续", 224),
        ("pause-retry", "重试", 400),
        ("pause-back", "返回", 576),
    )
    MAGIC_SCALE = 1.6   # x768(SD) → x480 预览换算

    def _draw_pause(self, sx, sy, screen_w, screen_h, scale):
        """在游玩画面之上绘制暂停界面（压暗 + 覆盖层 + 三个按钮）。

        官方规则（Skinning/Interface，osu! 指南）：
        - 先将游玩画面亮度降低约 70%（保留约 30%），再在其上叠加暂停元素
        - pause-overlay：Centre，建议 1366x768，不拉伸、满高 768px；
          预览中按高度铺满屏幕，宽度过大时仅显示中间部分、过小时保留透明侧边
        - pause-continue(224) / pause-retry(400) / pause-back(576)：Centre 锚在
          画面中心横线，纵坐标为 SD(x768) 高度，预览换算 ÷1.6（→ x480 的 140/250/360）
        - 按钮尺寸按 x768 基准 ÷1.6 缩小（与 HUD/舞台元素一致，1x 素材直接缩放）
        """
        cx = sx + screen_w / 2

        # 1) 游玩画面压暗约 70%（保留约 30% 原亮度，用 gray75 点阵近似），
        #    再叠加暂停覆盖层（而非整体直接盖住）
        self.canvas.create_rectangle(sx, sy, sx + screen_w, sy + screen_h,
                                     fill="#000000", stipple="gray75", outline="")

        # 2) 覆盖层（存在时绘制在半透明遮罩之上）：官方“不拉伸”——
        #    按 1x 原生尺寸 ÷1.6(×768→x480) 渲染并居中；不缩放填满，
        #    大图只显示中间、小图保留透明边框
        overlay = self._resolve_path(None, "pause-overlay")
        overlay_img = self._open_img_or_none(overlay) if overlay else None
        if overlay_img is not None and overlay_img.size[0] > 0 and overlay_img.size[1] > 0:
            iw, ih = overlay_img.size
            ow = max(1, int(iw / 1.6 * scale))
            oh = max(1, int(ih / 1.6 * scale))
            self.canvas.create_image(sx + screen_w / 2, sy + screen_h / 2,
                                     image=self._photo(overlay_img, ow, oh), anchor="center",
                                     tags=("pick:pause-overlay",))

        # 3) 三个按钮：Center 锚在画面中心，纵坐标按官方 SD 位置换算
        for base, label, sd_y in self.PAUSE_BUTTONS:
            y = sy + (sd_y / self.MAGIC_SCALE) * scale
            path = self._resolve_path(None, base)
            photo = None
            w = h = 0
            img = self._open_img_or_none(path) if path else None
            if img is not None and img.size[0] > 0 and img.size[1] > 0:
                w = max(1, int(img.size[0] / 1.6 * scale))
                h = max(1, int(img.size[1] / 1.6 * scale))
                photo = self._photo(img, w, h)
            if photo:
                self.canvas.create_image(cx, y, image=photo, anchor="center",
                                         tags=(f"pick:{base}",))
            else:
                self.canvas.create_text(cx, y, text=f"[{label}]", fill="#ffffff",
                                        font=("Microsoft YaHei UI",
                                              max(int(26 * scale / self.MAGIC_SCALE), 9),
                                              "bold"))

    # 失败界面按钮：官方仅「重试」与「返回」两个（中心 y≈SD: retry=400, back=576）
    FAIL_BUTTONS = (
        ("pause-retry", "重试", 400),
        ("pause-back", "返回", 576),
    )

    def _draw_fail(self, sx, sy, screen_w, screen_h, scale):
        """绘制独立的失败界面（新开一块屏幕，不绘制游玩画面）。

        官方规则（Skinning/Interface）：
        - fail-background：Centre，建议 1366x768，作失败界面背景，Cover 铺满整屏
        - 失败界面仅两个按钮：pause-retry（Center y=400）与 pause-back（Center y=576）
        - 按钮尺寸按 x768 基准 ÷1.6 换算（与 HUD/舞台元素一致）
        """
        # 背景：fail-background（优先）→ menu 背景 → 纯黑；Cover 铺满整屏成为独立屏幕
        img = None
        fb_path = self._img_path("fail-background")
        if fb_path:
            img = self._open_skin_image(fb_path)
        if img is None or img.size[0] <= 0 or img.size[1] <= 0:
            img = None
            fb_path = self._img_path("menu-background") or self._img_path("menu-bg")
            if fb_path:
                img = self._open_skin_image(fb_path)
        if img is not None and img.size[0] > 0 and img.size[1] > 0:
            iw, ih = img.size
            cover = max(screen_w / iw, screen_h / ih)
            nw, nh = max(1, int(iw * cover)), max(1, int(ih * cover))
            left, top = (nw - screen_w) // 2, (nh - screen_h) // 2
            img = img.resize((nw, nh), Image.LANCZOS)
            img = img.crop((left, top, left + screen_w, top + screen_h))
            self.canvas.create_image(sx, sy, image=self._photo(img, screen_w, screen_h),
                                     anchor="nw", tags=("pick:fail-background",))
        else:
            self.canvas.create_rectangle(sx, sy, sx + screen_w, sy + screen_h,
                                         fill="#000000", outline="")

        cx = sx + screen_w / 2
        for base, label, sd_y in self.FAIL_BUTTONS:
            y = sy + (sd_y / self.MAGIC_SCALE) * scale
            path = self._resolve_path(None, base)
            photo = None
            w = h = 0
            img = self._open_img_or_none(path) if path else None
            if img is not None and img.size[0] > 0 and img.size[1] > 0:
                w = max(1, int(img.size[0] / 1.6 * scale))
                h = max(1, int(img.size[1] / 1.6 * scale))
                photo = self._photo(img, w, h)
            if photo:
                self.canvas.create_image(cx, y, image=photo, anchor="center",
                                         tags=(f"pick:{base}",))
            else:
                self.canvas.create_text(cx, y, text=f"[{label}]", fill="#ffffff",
                                        font=("Microsoft YaHei UI",
                                              max(int(26 * scale / self.MAGIC_SCALE), 9),
                                              "bold"))

    def _draw_play_skip(self, sx, sy, screen_w, screen_h, scale):
        """绘制游玩界面的“跳过”按钮（play-skip，右下角）。

        官方（Skinning/Interface / Playfield）：play-skip 为乘法混合、
        BottomRight 定位、可动画、无固定尺寸。在休息段显示，仅游玩界面绘制。
        """
        if not self.skip_var.get():
            return
        path = self._resolve_path(None, "play-skip")
        img = self._open_img_or_none(path) if path else None
        if img is not None and img.size[0] > 0 and img.size[1] > 0:
            w = max(1, int(img.size[0] / 1.6 * scale))
            h = max(1, int(img.size[1] / 1.6 * scale))
            photo = self._photo(img, w, h)
            if photo:
                # BottomRight 定位：右下角贴边
                self.canvas.create_image(sx + screen_w, sy + screen_h,
                                         image=photo, anchor="se",
                                         tags=("pick:play-skip",))

    def _draw(self, vals):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw < 60 or ch < 60:
            return

        keys = int(_num(vals.get("Keys"), 4))
        keys = max(1, min(18, keys))
        layout = NOTE_LAYOUT.get(keys, ["1"] * keys)

        # 画面比例（16:9 / 16:10），据此在画布内拟合一块“屏幕”
        aspect = 16.0 / 9.0 if self.aspect_var.get() == "16:9" else 16.0 / 10.0
        margin = 20
        avail_w = cw - 2 * margin
        avail_h = ch - 2 * margin
        if avail_w / avail_h > aspect:
            screen_h = avail_h
            screen_w = avail_h * aspect
        else:
            screen_w = avail_w
            screen_h = avail_w / aspect
        sx = (cw - screen_w) / 2
        sy = (ch - screen_h) / 2

        # 游戏区域（屏幕）：高度固定 480 单位，宽度随画面比例变化；
        # 面板以 ColumnStart 从左侧绝对定位（因此 mania 面板整体偏左）
        scale = screen_h / 480.0

        def X(x):
            return sx + x * scale

        # 倒置（UpsideDown）：整个舞台垂直翻转，判定线/按键移向上方；
        # 键/音符图按 KeyFlipWhenUpsideDown / NoteFlipWhenUpsideDown 垂直翻转
        upside = vals.get("UpsideDown") in ("1", "true", "yes", True)
        flip_keys = upside and vals.get("KeyFlipWhenUpsideDown") not in ("0", "false", "no")
        flip_notes = upside and vals.get("NoteFlipWhenUpsideDown") not in ("0", "false", "no")
        # KeysUnderNotes：0=按键盖在音符上（默认），1=音符盖在按键上
        keys_under = vals.get("KeysUnderNotes") in ("1", "true", "yes", True)
        # SplitStages：把键位分成左右两个舞台，间距 StageSeparation
        split = vals.get("SplitStages") in ("1", "true", "yes", True) and keys > 1
        stage_sep = _num(vals.get("StageSeparation"), 40)
        # NoteBodyStyle：长条身体样式（v2.5+）0=拉伸，1=从顶级联，2=从底级联
        note_body_style = int(_choice(vals.get("NoteBodyStyle"), 1))
        # WidthForNoteHeightScale：列宽不同时音符高度的公共基准宽；
        # 未设置则取最窄列（官网默认行为）
        note_ref_w = _num(vals.get("WidthForNoteHeightScale"), 0)
        # ComboBurstStyle：连击图位置 0=左，1=右，2=两侧
        cb_style = int(_choice(vals.get("ComboBurstStyle"), 1))

        def Y(y):
            if upside:
                return sy + (480 - y) * scale
            return sy + y * scale

        col_start = _num(vals.get("ColumnStart"), 136)
        widths = _num_list(vals.get("ColumnWidth"), 30, keys)
        spacings = _num_list(vals.get("ColumnSpacing"), 0, keys)
        line_widths = _num_list(vals.get("ColumnLineWidth"), 2, keys + 1)
        hit_y = _num(vals.get("HitPosition"), 402)
        light_y = _num(vals.get("LightPosition"), 413)

        # 计算列矩形
        x = col_start
        cols = []  # (x0, x1)
        for i in range(keys):
            cols.append((x, x + widths[i]))
            x += widths[i] + spacings[i]
        # 分离舞台：右半列整体右移，两舞台间隔 StageSeparation
        half = keys // 2
        if split:
            x = cols[half - 1][1] + stage_sep
            for i in range(half, keys):
                cols[i] = (x, x + widths[i])
                x += widths[i] + spacings[i]
        note_ref_w = note_ref_w or min([w for w in widths if w > 0]) or 30
        stage_left = cols[0][0]
        stage_right = cols[-1][1]
        stage_w = stage_right - stage_left

        col_line = self._parse_rgba(vals.get("ColourColumnLine"), (255, 255, 255, 255))
        col_line_color = rgb_to_hex(col_line[:3]) if col_line[3] > 0 else None
        judge_line = self._parse_rgba(vals.get("ColourJudgementLine"), (255, 255, 255, 255))
        judge_line_color = rgb_to_hex(judge_line[:3])

        # 屏幕背景（游戏区域）：开启“背景”开关时优先使用皮肤的
        # menu-background / menu-bg（等比覆盖铺满整个屏幕、居中裁掉溢出部分，
        # 与官方行为一致），关闭或缺失时回退纯黑
        bg_photo = None
        if self.bg_var.get():
            bg_path = self._img_path("menu-background") or self._img_path("menu-bg")
            if HAS_PIL and bg_path:
                img = self._open_skin_image(bg_path)
                if img is not None:
                    iw, ih = img.size
                    if iw > 0 and ih > 0:
                        cover = max(screen_w / iw, screen_h / ih)
                        nw, nh = max(1, int(iw * cover)), max(1, int(ih * cover))
                        left, top = (nw - screen_w) // 2, (nh - screen_h) // 2
                        img = img.resize((nw, nh), Image.LANCZOS)
                        img = img.crop((left, top, left + screen_w, top + screen_h))
                        bg_photo = self._photo(img, screen_w, screen_h)
        if bg_photo:
            self.canvas.create_image(sx, sy, image=bg_photo, anchor="nw",
                                     tags=("pick:menu-background",))
        else:
            self.canvas.create_rectangle(sx, sy, sx + screen_w, sy + screen_h,
                                         fill="#000000", outline="")

        # 失败界面：独立新开一块屏幕（不绘制游玩画面与血条）
        if self.page_var.get() == "失败界面":
            self._draw_fail(sx, sy, screen_w, screen_h, scale)
            return

        # 血条（屏幕级 HUD，始终贴屏幕底边，倒置时不随舞台翻转）
        self._draw_scorebar(X(stage_right), sy + 480 * scale, scale)

        # 列底
        for i, (x0, x1) in enumerate(cols):
            rgba = self._parse_rgba(vals.get(f"Colour{i + 1}"), (0, 0, 0, 255))
            fill = rgb_to_hex(rgba[:3]) if rgba[3] > 0 else "#1c1c22"
            self.canvas.create_rectangle(X(x0), Y(0), X(x1), Y(480),
                                         fill=fill, outline="")

        # 列分隔线（宽度 + 颜色）：xK 共 x+1 条（左边界 + 各列间 + 右边界）
        line_xs = [cols[0][0]] + [c[1] for c in cols]
        for j, bx in enumerate(line_xs):
            lw = max(0.0, line_widths[j]) * scale
            if not col_line_color or lw <= 0:
                continue
            self.canvas.create_line(X(bx), Y(0), X(bx), Y(480),
                                    fill=col_line_color, width=max(1, int(lw)))

        # 小节线（barline）：每个小节开始时刻显示，横跨整个舞台。
        # 预览中展示在舞台中部（y=240，480 坐标系），避免被判定线处的
        # 接收器/头图遮挡；颜色 ColourBarline、厚度 BarlineHeight。
        # 皮肤将 Alpha 设为 0（如 ColourBarline: 0,0,0,0）时游戏内不显示，
        # 预览用灰色虚线标注其位置，便于编辑时看到小节线所在高度。
        barline_rgba = self._parse_rgba(vals.get("ColourBarline"), (255, 255, 255, 255))
        barline_h = max(0.0, _num(vals.get("BarlineHeight"), 1.2)) * scale
        if barline_rgba[3] <= 0:
            self.canvas.create_line(X(stage_left), Y(240), X(stage_right), Y(240),
                                    fill="#888888", width=1, dash=(4, 4))
        elif barline_h > 0:
            self.canvas.create_line(X(stage_left), Y(240), X(stage_right), Y(240),
                                    fill=rgb_to_hex(barline_rgba[:3]),
                                    width=max(1, int(barline_h)))

        # 舞台灯光（按键按下时的列光束，位于音符之下，高度为 LightPosition）
        # 只在“按压状态”的列展示（右半轨道 i >= keys//2，与按压接收器一致）
        # 颜色按每列 ColourLight 着色（官方 Multiplicative 混合，默认 55,255,255）
        light_path = self._resolve_path(vals.get("StageLight"), "mania-stage-light")
        if light_path:
            for i, (x0, x1) in enumerate(cols):
                if i < keys // 2:
                    continue
                img = self._open_img_or_none(light_path)
                photo = None
                if img is not None:
                    col_light = self._parse_rgba(vals.get(f"ColourLight{i + 1}"),
                                                 (55, 255, 255, 255))
                    photo = self._photo(self._tint(img, col_light[:3]),
                                        (x1 - x0) * scale, 30 * scale)
                if photo:
                    self.canvas.create_image(X(x0), Y(light_y) - 15 * scale,
                                             image=photo, anchor="nw",
                                             tags=("pick:mania-stage-light",))

        # 按键/接收器：从舞台底部贴底开始，上端无界限（图片多高就画多高）；
        # 宽度拉伸到轨道宽度、高度保持图片原逻辑高度不变。
        # 右半轨道（第 keys//2 列起）显示按压后的状态图 KeyImage{x}D
        # （官方：D 后缀为 pressed state，Origin Bottom，拉伸到列宽）。
        # 图层顺序由 KeysUnderNotes 决定（默认按键在音符之上）。
        def _draw_keys():
            for i, (x0, x1) in enumerate(cols):
                pressed = i >= keys // 2
                cmd = f"KeyImage{i}D" if pressed else f"KeyImage{i}"
                fallback = f"mania-key{layout[i]}D" if pressed else f"mania-key{layout[i]}"
                path = self._resolve_path(vals.get(cmd), fallback)
                photo, key_h = self._load_photo_stretch_width(
                    path, (x1 - x0) * scale, scale, flip_v=flip_keys)
                if photo:
                    # 倒置时舞台上下翻转：图像改以顶部锚定（从 Y(480) 对应的
                    # 屏幕顶部向下延伸），配合 flip_v 使按键图形朝向正确
                    self.canvas.create_image(X((x0 + x1) / 2), Y(480),
                                             image=photo, anchor="n" if upside else "s",
                                             tags=(f"pick:mania-key{layout[i]}{'D' if pressed else ''}",))
                elif self._show_default_on():
                    # 缺失按键：关闭“显示默认组件”则不绘制；开启则用默认灰色按键占位
                    self.canvas.create_rectangle(X(x0), Y(hit_y), X(x1), Y(480),
                                                 fill="#3a3a44", outline="#ffffff")

        if keys_under:
            _draw_keys()

        # 音符灯光（lightingN/lightingL）：官方位于音符图层之下（HitObjectArea 的
        # Underlay 下层，见 lazer ColumnHitObjectArea.cs），在判定线与轨道中心
        # 交点处显示。官网：单点/尾音符用 LightingN，长条用 LightingL，
        # Additive 混合；宽度由 LightingNWidth/LightingLWidth 覆盖，缺省用列宽
        lighting_n = self._resolve_path(vals.get("LightingN"), "lightingN")
        lighting_l = self._resolve_path(vals.get("LightingL"), "lightingL")
        n_widths = _num_list(vals.get("LightingNWidth"), 0, keys)
        l_widths = _num_list(vals.get("LightingLWidth"), 0, keys)
        for i, (x0, x1) in enumerate(cols):
            if i < keys // 2:
                continue  # 只在“按压状态”的列展示（与舞台灯光一致）
            if i == keys - 1:
                path = lighting_l
                w_override = l_widths[i]
            else:
                path = lighting_n
                w_override = n_widths[i]
            if not path:
                continue
            img = self._open_img_or_none(path)
            if img is None or img.size[0] <= 0:
                continue
            iw, ih = img.size
            wpx = w_override * scale if w_override > 0 else (x1 - x0) * scale
            hpx = max(1, int(ih * wpx / iw))
            photo = self._photo(img, max(1, int(wpx)), hpx)
            self.canvas.create_image(X((x0 + x1) / 2), Y(hit_y),
                                     image=photo, anchor="center",
                                     tags=("pick:lightingN" if i != keys - 1 else "pick:lightingL",))

        # 音符（判定线上方，模拟下落）。
        # 官网规则：音符高度以最窄列（或 WidthForNoteHeightScale）为公共基准，
        # 各列图片等基准缩放后横向压缩到本列宽度（列宽不同时高度一致）。
        # 最右列（keys-1）留作单独展示长条，不画普通音符
        note_h = 44.0
        for i, (x0, x1) in enumerate(cols):
            if i == keys - 1:
                continue
            path = self._resolve_path(vals.get(f"NoteImage{i}"), f"mania-note{layout[i]}")
            color = NOTE_COLORS[i % len(NOTE_COLORS)]
            img = self._open_img_or_none(path)
            photo = None
            if img is not None and img.size[0] > 0:
                iw, ih = img.size
                nh = max(1, int(ih * note_ref_w / iw * scale))
                photo = self._photo(img, max(1, int((x1 - x0) * scale)), nh,
                                    flip_v=flip_notes)
            for k in (1, 2, 3):
                ny = hit_y - k * 70
                if ny < 20:
                    continue
                if photo:
                    # 倒置时音符向下延伸（判定线在上），故以顶部锚定 + 翻转
                    self.canvas.create_image(X((x0 + x1) / 2), Y(ny),
                                             image=photo, anchor="n" if upside else "s",
                                             tags=(f"pick:mania-note{layout[i]}",))
                elif self._show_default_on():
                    # 缺失音符：关闭“显示默认组件”则不绘制；开启则用默认彩色方块占位
                    if upside:
                        self.canvas.create_rectangle(X(x0), Y(ny),
                                                     X(x1), Y(ny) + note_h * scale,
                                                     fill=color, outline="")
                    else:
                        self.canvas.create_rectangle(X(x0), Y(ny) - note_h * scale,
                                                     X(x1), Y(ny), fill=color, outline="")

        # 长条（LN / hold note）：展示在最右列，模拟按下后的长条
        # 官方摆放（头图 Origin Bottom 贴判定线，各图以 WidthForNoteHeightScale
        # 或最窄列为公共缩放基准，横向压缩到列宽）：
        # 从上到下 = 尾帽 cup（NoteImage{x}T）→ 身体（NoteImage{x}L）→ 头图（NoteImage{x}H）
        # - cup 位于 body 最上端：垂直中心与 body 顶边重合（一半露出、一半盖住 body）
        # - body 顶部完整显示（上面不截断），底部在头图中心线处截断
        # - 头图贴在判定线（HitPosition）上，body 延伸到头图中心处
        ln = keys - 1
        lx0, lx1 = cols[ln]
        ln_color = NOTE_COLORS[ln % len(NOTE_COLORS)]
        ln_len = 260.0                      # 长条视觉长度（480 坐标系单位）
        ln_w = (lx1 - lx0) * scale

        # 头图：贴判定线，高度按公共基准缩放、宽度拉伸到列宽
        head_path = self._resolve_path(vals.get(f"NoteImage{ln}H"),
                                       f"mania-note{layout[ln]}H")
        head_photo = None
        head_h = 0
        if head_path:
            img = self._open_img_or_none(head_path)
            if img is not None and img.size[0] > 0:
                iw, ih = img.size
                head_h = max(1, int(ih * note_ref_w / iw * scale))
                head_photo = self._photo(img, ln_w, head_h, flip_v=flip_notes)
        # 头图中心线（body 底部截断处）：head_h 是像素，换算回 480 单位再与 hit_y 相减
        head_cx_y = hit_y - (head_h / scale) / 2
        ln_top = head_cx_y - ln_len         # body / cup 顶端

        # 身体：以公共基准等比缩放（宽 → 按基准缩放，横向拉伸到列宽），
        # 显示从头图中心线向上 ln_len 的长度，样式由 NoteBodyStyle 决定：
        # - 0=拉伸：单张图非等比拉伸填满整个长条
        # - 1=从顶（默认）：单张不够时向下平铺，纹理从顶部开始
        # - 2=从底：单张不够时从判定线（头图中心）向上平铺
        # 颜色按 ColourHold 覆盖（官方 lazer：覆盖长条身体颜色）
        body_photo = None
        body_src_w = 0                      # body 源图宽度（供 cup 同基准缩放）
        body_path = self._resolve_path(vals.get(f"NoteImage{ln}L"),
                                       f"mania-note{layout[ln]}L")
        if body_path:
            hold_rgba = self._parse_rgba(vals.get("ColourHold"), (255, 255, 255, 255))
            body_img, body_src_w = self._build_hold_body(
                body_path, note_body_style, ln_w, ln_len * scale,
                note_ref_w, scale, hold_rgba)
            if body_img is not None:
                body_photo = self._photo(body_img, ln_w, ln_len * scale,
                                         flip_v=flip_notes)

        # 尾帽 cup：与 body 同一缩放基准等比放大，故比 body 宽（素材 holdcap
        # 256px > holdbody 138px），中心对齐列、垂直中心在 body 顶边，
        # 一半伸出 body 上方、一半盖住 body 顶部；无 body 时缩放到列宽
        tail_photo = None
        tail_path = self._resolve_path(vals.get(f"NoteImage{ln}T"),
                                       f"mania-note{layout[ln]}T")
        if tail_path:
            img = self._open_img_or_none(tail_path)
            if img is not None:
                iw, ih = img.size
                if iw > 0 and ih > 0:
                    k = note_ref_w / body_src_w if body_src_w else note_ref_w / iw
                    tw = max(1, int(iw * k * scale))
                    th = max(1, int(ih * k * scale))
                    tail_photo = self._photo(img, tw, th, flip_v=flip_notes)
        if tail_photo is None and head_path:
            # 无尾图：用头图垂直翻转（官方 v2.5+ 默认 NoteFlipWhenUpsideDownT），
            # 尺寸与头图一致（等比缩放到列宽）
            img = self._open_img_or_none(head_path)
            if img is not None:
                img = img.transpose(Image.FLIP_TOP_BOTTOM)
                tail_photo = self._photo(img, ln_w, head_h, flip_v=flip_notes)

        if body_photo or head_photo or tail_photo:
            if body_photo:
                # body 合成图覆盖舞台坐标 [ln_top, head_cx_y]：
                # 正立时以顶部锚定在 ln_top；倒置时舞台翻转，合成图也已 flip_v，
                # 视觉顶（翻转后 = 头端）应锚定在头端位置 head_cx_y
                self.canvas.create_image(X((lx0 + lx1) / 2), Y(head_cx_y if upside else ln_top),
                                         image=body_photo, anchor="n",
                                         tags=(f"pick:mania-note{layout[ln]}L",))
            if head_photo:
                # 头图底边贴判定线：正立锚 "s"，倒置舞台翻转后改锚 "n"（配合 flip_v）
                self.canvas.create_image(X((lx0 + lx1) / 2), Y(hit_y),
                                         image=head_photo, anchor="n" if upside else "s",
                                         tags=(f"pick:mania-note{layout[ln]}H",))
            if tail_photo:
                self.canvas.create_image(X((lx0 + lx1) / 2), Y(ln_top),
                                         image=tail_photo, anchor="center",
                                         tags=(f"pick:mania-note{layout[ln]}T",))
        else:
            # 全部缺失：关闭“显示默认组件”则不绘制；开启则用默认长条占位（ln_color + 白色头部）
            if self._show_default_on():
                self.canvas.create_rectangle(X(lx0), Y(ln_top), X(lx1), Y(hit_y),
                                             fill=ln_color, outline="")
                self.canvas.create_rectangle(X(lx0), Y(hit_y) - 8 * scale,
                                             X(lx1), Y(hit_y), fill="#ffffff", outline="")

        if not keys_under:
            _draw_keys()

        # 判定线（官方位于按键之上、StageForeground 之下，覆盖音符/长条）
        # 按舞台宽等比缩放（保持宽高比，避免原图被压扁到不可见）；
        # 分离模式每个舞台各画一条
        hint_path = self._resolve_path(vals.get("StageHint"), "mania-stage-hint")
        if split:
            stage_ranges = [(cols[0][0], cols[half - 1][1]),
                            (cols[half][0], cols[-1][1])]
        else:
            stage_ranges = [(stage_left, stage_right)]
        for sl, sr in stage_ranges:
            sw = sr - sl
            photo = None
            if hint_path:
                photo, _ = self._load_photo_fit_width(hint_path, sw * scale)
            if photo:
                self.canvas.create_image(X((sl + sr) / 2), Y(hit_y),
                                         image=photo, anchor="center",
                                         tags=("pick:mania-stage-hint",))
            else:
                self.canvas.create_line(X(sl), Y(hit_y), X(sr), Y(hit_y),
                                        fill=judge_line_color, width=2)
            # 额外的判定提示线（JudgementLine 命令）
            if vals.get("JudgementLine") in ("1", "true", "yes", True):
                self.canvas.create_line(X(sl), Y(hit_y), X(sr), Y(hit_y),
                                        fill=judge_line_color, width=1)

        # 警告箭头（WarningArrow）：开始前显示在场地中央，倒置时水平翻转
        warning_path = self._resolve_path(vals.get("WarningArrow"), "mania-warningarrow")
        if self.warning_var.get() and warning_path:
            img = self._open_img_or_none(warning_path)
            if img is not None and img.size[0] > 0:
                iw, ih = img.size
                wpx = max(1, int(stage_w * 0.4 * scale))
                hpx = max(1, int(ih * wpx / iw))
                photo = self._photo(img, wpx, hpx, flip_h=upside)
                self.canvas.create_image(X((stage_left + stage_right) / 2), Y(480 * 0.35),
                                         image=photo, anchor="center",
                                         tags=("pick:mania-warningarrow",))

        # 舞台左右边框（官方 StageForeground 层：覆盖按键/音符，位于 HUD 之下；
        # 倒置时图像不翻转）。分离模式每舞台各画一对（左缘 stage-left、右缘 stage-right）
        left_path = self._resolve_path(vals.get("StageLeft"), "mania-stage-left")
        right_path = self._resolve_path(vals.get("StageRight"), "mania-stage-right")
        side_edges = []
        if split:
            side_edges = [(cols[0][0], True), (cols[half - 1][1], False),
                          (cols[half][0], True), (cols[-1][1], False)]
        else:
            side_edges = [(cols[0][0], True), (cols[-1][1], False)]
        for edge_x, align_right in side_edges:
            if align_right:
                self._draw_stage_side(left_path, X(edge_x), sy, 480 * scale,
                                      align_right=True, tag="mania-stage-left")
            else:
                self._draw_stage_side(right_path, X(edge_x), sy, 480 * scale,
                                      align_right=False, tag="mania-stage-right")

        # 舞台底部（装饰层：绘制在左右舞台之前/之后，位于 HUD 之下——
        # 游戏中属于 StageForeground 层，分数/acc 等 HUD 元素绘制在其上；
        # 倒置时显示在舞台顶部，但图像内容不垂直翻转。
        # 分离模式每个舞台各一张；绘制在左右舞台之上以覆盖其边缘）
        bottom_path = self._resolve_path(vals.get("StageBottom"), "mania-stage-bottom")
        if split:
            for sl, sr in [(cols[0][0], cols[half - 1][1]),
                           (cols[half][0], cols[-1][1])]:
                self._draw_stage_bottom(bottom_path, X((sl + sr) / 2), Y(480), scale,
                                        upside=upside, tag="mania-stage-bottom")
        else:
            self._draw_stage_bottom(bottom_path, X((stage_left + stage_right) / 2),
                                    Y(480), scale, upside=upside,
                                    tag="mania-stage-bottom")

        # 连击图（官方位于 StageForeground 之上、灯光之下，HUD 级；
        # 位置由 ComboBurstStyle 决定：0=左，1=右，2=两侧；右侧时水平翻转）
        # 预览 x480 中高度 = 图片 1x 逻辑高度 / 1.6（缺失回退 56/1.6）
        if self.cb_var.get():
            if cb_style == 0:
                cb_sides = [(X(stage_left) - 6 * scale, "se", False)]
            elif cb_style == 2:
                cb_sides = [(X(stage_left) - 6 * scale, "se", False),
                            (X(stage_right) + 6 * scale, "sw", True)]
            else:
                cb_sides = [(X(stage_right) + 6 * scale, "sw", True)]
            comboburst = self._img_path("comboburst-mania")
            for edge_x, anchor, flip_h in cb_sides:
                photo = None
                if comboburst:
                    cb_img = self._open_skin_image(comboburst)
                    cb_h = (cb_img.size[1] / 1.6 if cb_img else 56 / 1.6) * scale
                    # 倒置时连击图随舞台垂直翻转：锚点 s→n，图像 flip_v
                    photo, _ = self._load_photo_fit_height(comboburst, cb_h, flip_h=flip_h,
                                                           flip_v=upside)
                disp_anchor = anchor if not upside else anchor.replace("s", "n")
                if photo:
                    self.canvas.create_image(edge_x, Y(hit_y), image=photo,
                                             anchor=disp_anchor,
                                             tags=("pick:comboburst-mania",))
                # 连击图为可选装饰：缺失时完全不绘制占位（“显示默认组件”开关对连击图不生效）

        # ColumnRight 边界标记：仅当设置值超出当前舞台右缘时显示虚线
        col_right = _num(vals.get("ColumnRight"), 19)
        if col_right > stage_right + 1:
            self.canvas.create_line(X(col_right), Y(0), X(col_right), Y(480),
                                    fill="#ffffff", width=1, dash=(2, 3))

        # ---- HUD：分数 / 准确度 / 连击计数 / 判定评分 / 血条 ----
        stage_cx = X((stage_left + stage_right) / 2)
        score_prefix = self.app.ini.get("Fonts", "ScorePrefix") or "score"
        combo_prefix = self.app.ini.get("Fonts", "ComboPrefix") or "score"

        # 分数 / 准确度（屏幕右上角）
        # HUD 数字与连击/判定一致：官方在 x768 基准中按图片 1x 逻辑尺寸显示，
        # 预览 x480 坐标系中高度 = 图片 1x 逻辑高度 / 1.6（缺失时回退 26/1.6）；
        # acc 与分数共用 ScorePrefix 字体，但 acc 高度 = 分数的 0.6 倍
        # （lazer：LegacyAccuracyCounter Scale = 0.6*0.96，LegacyScoreCounter = 0.96）。
        # 数字间距由 [Fonts] ScoreOverlap 决定（x768 基准值，换算到 x480 需 ÷1.6）。
        # 官方位置（lazer LegacyHUDOverlay，x768 基准）：
        #   分数：Anchor TopRight，Position(-14, 10)；acc：Position(-14, 45)。
        # 换算到 x480 预览坐标系（÷1.6）后乘画布 scale。
        score_img = self._open_skin_image(self._digit_path(score_prefix, "1"))
        score_h = (score_img.size[1] / 1.6 if score_img else 26 / 1.6) * scale
        score_overlap = _num(self.app.ini.get("Fonts", "ScoreOverlap"), 0) / 1.6 * scale
        hud_right = 14 / 1.6 * scale        # 距画布右缘（x768 的 14）
        self._draw_number(self.score_text_var.get(), score_prefix,
                          sx + screen_w - hud_right, sy + 10 / 1.6 * scale,
                          "right", score_h, score_overlap, tag="score-0")

        acc_h = score_h * 0.6
        self._draw_number(self.acc_text_var.get(), score_prefix,
                          sx + screen_w - hud_right,
                          sy + 45 / 1.6 * scale,
                          "right", acc_h, score_overlap, tag="score-0")

        # 连击计数（场地水平居中，ComboPosition 为数字中心 Y）
        # 官方规则：游戏内 mania 连击数字会被缩小（skin.ini v2.4 "Downscale combo
        # counter"），等价于 lazer 的 x768 画布（STABLE_MAGIC_SCALE_FACTOR=1.6）
        # 中按图片 1x 逻辑尺寸绘制，因此 x480 坐标系中的显示高度 =
        # 图片 1x 逻辑高度 / 1.6（缺失时回退 44/1.6）。
        combo_y = _num(vals.get("ComboPosition"), 111)
        combo_img = self._open_skin_image(self._digit_path(combo_prefix, "1"))
        combo_h = (combo_img.size[1] / 1.6 if combo_img else 44 / 1.6) * scale
        combo_overlap = _num(self.app.ini.get("Fonts", "ComboOverlap"), 0) / 1.6 * scale
        self._draw_number(self.combo_text_var.get(), combo_prefix, stage_cx,
                          Y(combo_y) - combo_h / 2, "center", combo_h, combo_overlap,
                          tag="combo-0")

        # 判定评分 / hitburst（垂直 = ScorePosition；水平默认场地居中，
        # 分离舞台且 SeparateScore=1 时只显示在得分的那侧舞台，预览取右舞台）
        # 同样按官方 "Downscale ... hitbursts" 规则：显示高度 = 图片 1x 逻辑高度 / 1.6。
        # 图片按“数值”对话框中选中的评分值查找（300g/300/200/100/50/miss）。
        score_y = _num(vals.get("ScorePosition"), 300)
        hb_cx = stage_cx
        if split and vals.get("SeparateScore") in ("1", "true", "yes", True):
            hb_cx = X((cols[half][0] + cols[-1][1]) / 2)
        hit_value = self.hit_text_var.get()
        hitburst_path = None
        if hit_value in self.HIT_LOOKUP:
            # 每个判定评分都有独立的 skin.ini 命令（Hit300g/Hit300/Hit200/...），
            # 读取对应命令的值作为优先路径
            ini_key = self.HIT_INI_KEYS.get(hit_value)
            ini_path = vals.get(ini_key) if ini_key else None
            for base in self.HIT_LOOKUP[hit_value]:
                hitburst_path = self._resolve_path(ini_path, base)
                if hitburst_path:
                    break
        if hitburst_path:
            hb_img = self._open_skin_image(hitburst_path)
            hb_h = (hb_img.size[1] / 1.6 if hb_img else 40 / 1.6) * scale
            photo, _ = self._load_photo_fit_height(hitburst_path, hb_h)
            if photo:
                hb_tag = self.HIT_LOOKUP[hit_value][0] if hit_value in self.HIT_LOOKUP else "mania-hit"
                self.canvas.create_image(hb_cx, Y(score_y), image=photo,
                                         anchor="center", tags=(f"pick:{hb_tag}",))
        else:
            if self._show_default_on():
                # 缺失判定图片：“显示默认组件”开启时用默认文字评分显示（渲染保持原样）
                self.canvas.create_text(hb_cx, Y(score_y), text=hit_value,
                                        fill="#ffd54f",
                                        font=("Microsoft YaHei UI",
                                              max(int(30 * scale / 1.6), 8), "bold"))

        flags = []
        if upside:
            flags.append("倒置")
        if split:
            flags.append(f"分离({int(stage_sep)})")
        if note_body_style:
            flags.append(f"长条样式{note_body_style}")
        if cb_style != 1:
            flags.append("连击图" + ("左" if cb_style == 0 else "两侧"))
        self.info_var.set(
            f"{keys}K | {self.aspect_var.get()} | 判定线 {int(hit_y)} | 列起点 {int(col_start)} "
            f"| 列宽 {'/'.join(str(int(w)) for w in widths)}"
            + (" | " + " | ".join(flags) if flags else ""))

        # 页面切换：游玩界面在 HUD 之上绘制右下角“跳过”按钮
        if self.page_var.get() == "游玩界面":
            self._draw_play_skip(sx, sy, screen_w, screen_h, scale)
        # 暂停页面在游玩画面之上绘制覆盖层与按钮
        if self.page_var.get() == "暂停界面":
            self._draw_pause(sx, sy, screen_w, screen_h, scale)


# ---------------------------------------------------------------------------
# 主窗口
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # 读取上次保存的设置（主题/导入策略/缺失方块/上次皮肤）
        self.settings = load_settings()
        theme = self.settings.get("theme")
        if theme in THEMES:
            setup_style(self, theme)
        else:
            setup_style(self)
        self.title("OsuSkinMaker v0.0.4")
        self.minsize(1000, 680)
        self.skin_folder = None
        self.ini = SkinIni()
        self.manager = None
        self.theme_var = tk.StringVar(value=current_theme())
        # 导入素材的 @2x 处理策略：hd=直接 @2x / normal=直接原图 / ask=每次询问
        hd_default = self.settings.get("hd_default", "ask")
        self.import_hd_var = tk.StringVar(
            value=hd_default if hd_default in ("hd", "normal", "ask") else "ask")
        # 预览中缺失组件是否显示“默认组件”（默认开启；兼容旧字段 missing_block）
        self.show_default_var = tk.BooleanVar(
            value=bool(self.settings.get("show_default",
                                         self.settings.get("missing_block", True))))
        # 游玩预览点击组件联动选中元素管理中的对应元素（默认关闭）
        self.click_select_var = tk.BooleanVar(
            value=bool(self.settings.get("click_select", False)))
        # 元素管理是否按当前预览界面过滤分类（默认开启；关闭则任意界面显示全部元素）
        self.enable_category_var = tk.BooleanVar(
            value=bool(self.settings.get("enable_category", True)))
        # 编辑 skin.ini 的方式：path=直接导入路径 / copy=复制到皮肤子目录
        mode = self.settings.get("ini_import_mode", "path")
        self.ini_import_mode_var = tk.StringVar(
            value=mode if mode in ("path", "copy") else "path")
        # copy 模式的目标文件夹名（默认 mania）
        self.ini_import_folder_var = tk.StringVar(
            value=self.settings.get("ini_import_folder", "mania"))
        self.ini_import_folder_var.trace_add(
            "write", lambda *a: self._persist_settings())
        self._build_toolbar()
        self._build_main()
        self._bind_notebook_change()
        self._restore_window()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- 工具栏 ------------------------------------------------------------
    def _build_toolbar(self):
        # 顶部工具栏整体卡片化：panel 底色容器 + 统一内边距
        bar = ttk.Frame(self, style="Card.TFrame", padding=(12, 8))
        bar.pack(fill="x", padx=8, pady=(8, 0))

        # 文件操作组
        file_grp = ttk.Frame(bar, style="Card.TFrame")
        file_grp.pack(side="left")
        ttk.Button(file_grp, text=" 打开皮肤 ", command=self.open_skin,
                   style="Tool.TButton").pack(side="left", padx=(0, 4))
        ttk.Button(file_grp, text=" 新建 ", command=self.new_skin,
                   style="Tool.TButton").pack(side="left", padx=(0, 4))
        # 主操作：强调色按钮
        ttk.Button(file_grp, text=" 保存 ", command=self.save_ini,
                   style="Accent.TButton").pack(side="left")
        ttk.Button(file_grp, text=" 文件夹 ", command=self.open_skin_folder,
                   style="Tool.TButton").pack(side="left", padx=(4, 0))

        # 分隔
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=12, pady=4)

        # 视图组
        view_grp = ttk.Frame(bar, style="Card.TFrame")
        view_grp.pack(side="left")
        ttk.Button(view_grp, text=" 设置 ", command=self._open_settings,
                   style="Tool.TButton").pack(side="left")

        # 当前皮肤路径（高亮卡片）
        self.path_var = tk.StringVar(value="（未打开皮肤）")
        self.path_card = tk.Frame(bar, bg=theme_color("surface"),
                                  highlightbackground=theme_color("border"),
                                  highlightthickness=1)
        self.path_card.pack(side="right", padx=(12, 0))
        self.path_label = tk.Label(self.path_card, textvariable=self.path_var,
                                   bg=theme_color("surface"),
                                   fg=theme_color("text_secondary"),
                                   font=("Microsoft YaHei UI", 9), padx=10, pady=4)
        self.path_label.pack()

    def _apply_theme(self, name):
        """应用主题（浅色/深色），由设置弹窗调用。"""
        if name not in THEMES:
            return
        setup_style(self, name)
        self.theme_var.set(name)
        # 更新硬编码 tk 控件颜色（ttk 样式已由 setup_style 自动刷新）
        self.path_card.configure(bg=theme_color("surface"),
                                 highlightbackground=theme_color("border"))
        self.path_label.configure(bg=theme_color("surface"),
                                  fg=theme_color("text_secondary"))
        # 递归刷新所有 ScrollableFrame 的画布背景（皮肤编辑页等）
        def _fix_canvases(widget):
            for w in widget.winfo_children():
                if getattr(w, "_is_scroll_canvas", False):
                    w.configure(bg=theme_color("bg"))
                _fix_canvases(w)
        _fix_canvases(self)
        self.settings["theme"] = name
        save_settings(self.settings)
        self._refresh_preview()

    # -- 设置持久化 --------------------------------------------------------
    def _persist_settings(self):
        """把当前设置（主题/导入策略/缺失方块/编辑方式/上次皮肤）写入 settings.json。"""
        self.settings["theme"] = self.theme_var.get()
        self.settings["hd_default"] = self.import_hd_var.get()
        self.settings["show_default"] = bool(self.show_default_var.get())
        self.settings["click_select"] = bool(self.click_select_var.get())
        self.settings["enable_category"] = bool(self.enable_category_var.get())
        self.settings["ini_import_mode"] = self.ini_import_mode_var.get()
        self.settings["ini_import_folder"] = self.ini_import_folder_var.get()
        # 记录窗口大小/位置/最大化状态与各面板比例（sash 存相对比例）
        try:
            self.settings["win_state"] = self.state()
            self.settings["win_geometry"] = self.geometry()
            if getattr(self, "_main_paned", None):
                w = self._main_paned.winfo_width()
                s = self._main_paned.sashpos(0)
                if w > 0 and s:
                    self.settings["main_sash_ratio"] = round(s / w, 4)
            ep = getattr(self, "element_panel", None)
            if ep and getattr(ep, "paned", None):
                w = ep.paned.winfo_width()
                s = ep.paned.sashpos(0)
                if w > 0 and s:
                    self.settings["element_sash_ratio"] = round(s / w, 4)
        except Exception:
            pass
        if getattr(self, "skin_folder", None):
            self.settings["last_skin"] = self.skin_folder
        # 记录预览状态：页面类型、显示开关、比例与自定义数值
        sp = getattr(self, "stage_preview", None)
        if sp is not None:
            self.settings["preview_page"] = sp.page_var.get()
            self.settings["preview_bg"] = bool(sp.bg_var.get())
            self.settings["preview_cb"] = bool(sp.cb_var.get())
            self.settings["preview_warning"] = bool(sp.warning_var.get())
            self.settings["preview_skip"] = bool(sp.skip_var.get())
            self.settings["preview_aspect"] = sp.aspect_var.get()
            self.settings["preview_score"] = sp.score_text_var.get()
            self.settings["preview_acc"] = sp.acc_text_var.get()
            self.settings["preview_combo"] = sp.combo_text_var.get()
            self.settings["preview_hit"] = sp.hit_text_var.get()
        save_settings(self.settings)

    def _on_close(self):
        """关闭窗口：先保存展开状态与设置再退出。"""
        ep = getattr(self, "element_panel", None)
        if ep is not None:
            ep._save_open_state()
        self._persist_settings()
        self.destroy()

    def _on_setting_changed(self):
        """设置弹窗中的选项变更：保存设置并刷新预览/元素列表。"""
        self._persist_settings()
        self.stage_preview.refresh()
        ep = getattr(self, "element_panel", None)
        if ep is not None:
            ep.refresh()

    def select_element(self, filename):
        """联动选中元素管理列表中的指定元素（由游玩预览点击触发）。"""
        ep = getattr(self, "element_panel", None)
        if ep is not None:
            ep.select_element(filename)

    def _open_skin_path(self, folder):
        """加载指定皮肤文件夹（打开按钮、新建完成、启动恢复共用）。"""
        self.skin_folder = folder
        self.path_var.set(folder)
        self.manager = SkinManager(folder)
        self._load_ini()
        self.settings["last_skin"] = folder
        save_settings(self.settings)

    def _restore_last_skin(self):
        """启动时自动打开上次编辑的皮肤（仅当文件夹仍存在）。"""
        folder = self.settings.get("last_skin")
        if folder and os.path.isdir(folder):
            try:
                self._open_skin_path(folder)
            except Exception:
                pass

    def _restore_window(self):
        """恢复上次退出时的窗口大小/位置/最大化状态；无记录则默认最大化。

        面板比例（sash）需等布局稳定后再恢复。
        """
        if self.settings.get("win_state") == "zoomed":
            self.state("zoomed")
        else:
            g = self.settings.get("win_geometry")
            if g:
                try:
                    self.geometry(g)
                except Exception:
                    self.state("zoomed")
            else:
                self.state("zoomed")
        self.after(120, self._restore_sashes, 0)

    def _restore_sashes(self, _attempt=0):
        """恢复各 PanedWindow 的分隔条比例（主窗口 / 元素管理）。

        用相对比例换算成当前窗口宽度下的像素位置，适应不同屏幕/窗口尺寸。
        布局未稳定时设置可能被覆盖，最多自动重试 5 次。
        """
        self.update_idletasks()
        pairs = []
        if getattr(self, "_main_paned", None):
            pairs.append((self._main_paned, "main_sash_ratio"))
        ep = getattr(self, "element_panel", None)
        if ep and getattr(ep, "paned", None):
            pairs.append((ep.paned, "element_sash_ratio"))
        for paned, key in pairs:
            r = self.settings.get(key)
            w = paned.winfo_width()
            if isinstance(r, (int, float)) and 0 < r < 1 and w > 0:
                try:
                    paned.sashpos(0, int(w * r))
                except Exception:
                    pass
        if _attempt < 5:
            self.after(300, self._restore_sashes, _attempt + 1)

    def _open_settings(self):
        """打开设置弹窗（模态）。窗口可自由缩放，内容超长时右侧出现滚动条。"""
        win = tk.Toplevel(self)
        win.title("设置")
        w, h = 1060, 720
        win.geometry(f"{w}x{h}")
        win.resizable(True, True)
        win.minsize(600, 400)
        win.transient(self)
        win.grab_set()
        # 在父窗口正中央弹出
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        # 可滚动内容区：窗口缩小时右侧出现滚动条
        body = ScrollableFrame(win)
        body.pack(fill="both", expand=True, padx=16, pady=16)
        body.canvas.configure(bg=theme_color("bg"))

        # 主题（原工具栏主题切换移入此处）
        theme_card = ttk.Frame(body.inner, style="Card.TFrame", padding=10)
        theme_card.pack(fill="x")
        ttk.Label(theme_card, text="主题", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(theme_card, text="界面配色方案",
                  style="CardSecondary.TLabel").pack(anchor="w", pady=(0, 6))
        theme_row = ttk.Frame(theme_card)
        theme_row.pack(anchor="w")
        for name, label in (("light", "浅色"), ("dark", "深色")):
            ttk.Radiobutton(theme_row, text=label, value=name,
                            variable=self.theme_var,
                            command=lambda: self._apply_theme(self.theme_var.get())
                            ).pack(side="left", padx=(0, 12))

        # 编辑 skin.ini 的方式（点击“浏览”后的处理）
        edit_card = ttk.Frame(body.inner, style="Card.TFrame", padding=10)
        edit_card.pack(fill="x", pady=(12, 0))
        ttk.Label(edit_card, text="编辑方式",
                  style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(edit_card, text="点击“浏览”选择素材后的处理方式",
                  style="CardSecondary.TLabel").pack(anchor="w", pady=(0, 6))
        edit_row = ttk.Frame(edit_card)
        edit_row.pack(anchor="w")
        for val, label, desc in (
                ("path", "直接导入路径", "把素材在皮肤内的相对路径写入 skin.ini（原方式）"),
                ("copy", "复制到文件夹", "把素材复制到皮肤下的文件夹，再写入相对路径")):
            col = ttk.Frame(edit_row, style="Card.TFrame")
            col.pack(side="left", padx=(0, 24))
            ttk.Radiobutton(col, text=label, value=val,
                            variable=self.ini_import_mode_var,
                            command=self._persist_settings).pack(anchor="w")
            ttk.Label(col, text=desc,
                      style="Secondary.TLabel").pack(anchor="w")
        folder_row = ttk.Frame(edit_card)
        folder_row.pack(anchor="w", pady=(6, 0))
        ttk.Label(folder_row, text="目标文件夹：",
                  style="Secondary.TLabel").pack(side="left")
        ttk.Entry(folder_row, textvariable=self.ini_import_folder_var,
                  width=18).pack(side="left", padx=(4, 0))
        ttk.Label(folder_row, text="复制到 skin 根目录下的此文件夹",
                  style="Secondary.TLabel").pack(side="left", padx=(8, 0))

        # 导入素材（添加/替换组件时对 @2x 的默认处理）
        import_card = ttk.Frame(body.inner, style="Card.TFrame", padding=10)
        import_card.pack(fill="x", pady=(12, 0))
        ttk.Label(import_card, text="导入素材",
                  style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(import_card, text="添加/替换组件时默认如何处理 @2x",
                  style="CardSecondary.TLabel").pack(anchor="w", pady=(0, 6))
        import_row = ttk.Frame(import_card)
        import_row.pack(anchor="w")
        for val, label, desc in (
                ("hd", "@2x", "默认标记为高清，复制为 元素名@2x.png"),
                ("normal", "原图", "默认按原图复制为 元素名.png"),
                ("ask", "自行确认", "每次导入时询问是否添加 @2x")):
            col = ttk.Frame(import_row, style="Card.TFrame")
            col.pack(side="left", padx=(0, 24))
            ttk.Radiobutton(col, text=label, value=val,
                            variable=self.import_hd_var,
                            command=self._persist_settings).pack(anchor="w")
            ttk.Label(col, text=desc,
                      style="Secondary.TLabel").pack(anchor="w")

        # 预览显示（缺失组件的显示方式）
        preview_card = ttk.Frame(body.inner, style="Card.TFrame", padding=10)
        preview_card.pack(fill="x", pady=(12, 0))
        ttk.Label(preview_card, text="预览显示",
                  style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(preview_card, text="游玩预览中缺失组件的显示与交互方式",
                  style="CardSecondary.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Checkbutton(preview_card, text="缺失的组件显示默认组件",
                        variable=self.show_default_var,
                        command=self._on_setting_changed
                        ).pack(anchor="w")
        ttk.Label(preview_card, text="开启后：舞台、按键、音符、判定等组件缺失时以默认样式显示；关闭则不显示这些缺失组件",
                  style="Secondary.TLabel").pack(anchor="w")
        ttk.Checkbutton(preview_card, text="点击预览中的组件联动选中元素管理中的对应元素",
                        variable=self.click_select_var,
                        command=self._on_setting_changed
                        ).pack(anchor="w", pady=(10, 0))
        ttk.Label(preview_card, text="开启后：在左侧预览画面上点击某个组件，右侧“元素管理”列表会自动选中对应元素；双击可切换被遮挡的下一层组件",
                  style="Secondary.TLabel").pack(anchor="w")
        ttk.Checkbutton(preview_card, text="元素管理按当前预览界面分类显示",
                        variable=self.enable_category_var,
                        command=self._on_setting_changed
                        ).pack(anchor="w", pady=(10, 0))
        ttk.Label(preview_card, text="开启后：元素管理仅显示当前界面（游玩/暂停/失败/结算/选歌）的元素；关闭则任意界面都显示全部元素（仍按树状分组）",
                  style="Secondary.TLabel").pack(anchor="w")

        # TODO: 其余设置项——组件/游玩预览背景色、编辑方式（导入路径/复制到
        #       mania 目录）等
        ttk.Label(body.inner, text="更多设置项开发中……",
                  style="Secondary.TLabel").pack(anchor="w", pady=(16, 0))

    def _build_main(self):
        main = self._main_paned = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # 左侧：游玩预览（占 5/6）
        self.stage_preview = StagePreview(main, self)
        main.add(self.stage_preview, weight=5)

        # 右侧：元素管理 + skin.ini 编辑（占 1/6，各标签页平分）
        self.notebook = nb = ttk.Notebook(main)
        main.add(nb, weight=1)

        # 元素管理页
        self.element_panel = ElementPanel(nb, self)
        nb.add(self.element_panel, text="元素管理")

        # skin.ini 编辑页（内容包一层 padding，留出统一边距）
        self.ini_tab = ini_tab = ttk.Frame(nb, padding=8)
        nb.add(ini_tab, text="skin.ini 编辑")
        self.ini_sub = sub = ttk.Notebook(ini_tab)
        sub.pack(fill="both", expand=True)

        self.gen_frame = gen_frame = ScrollableFrame(sub)
        sub.add(gen_frame, text="General")
        self.general_form = Form(gen_frame.inner,
                                 lambda k: self.ini.get("General", k),
                                 lambda k, v: self.ini.set("General", k, v),
                                 skin_folder_getter=lambda: self.skin_folder)
        self.general_form.set_known(GENERAL_COMMANDS)
        for c in GENERAL_COMMANDS:
            self.general_form.add(c)
        self.general_form.load()

        self.col_frame = col_frame = ScrollableFrame(sub)
        sub.add(col_frame, text="Colours")
        self.colour_form = Form(col_frame.inner,
                                lambda k: self.ini.get("Colours", k),
                                lambda k, v: self.ini.set("Colours", k, v),
                                skin_folder_getter=lambda: self.skin_folder)
        self.colour_form.set_known(COLOUR_COMMANDS)
        for c in COLOUR_COMMANDS:
            self.colour_form.add(c)
        self.colour_form.load()

        self.font_frame = font_frame = ScrollableFrame(sub)
        sub.add(font_frame, text="Fonts")
        self.font_form = Form(font_frame.inner,
                              lambda k: self.ini.get("Fonts", k),
                              lambda k, v: self.ini.set("Fonts", k, v),
                              skin_folder_getter=lambda: self.skin_folder)
        self.font_form.set_known(FONT_COMMANDS)
        for c in FONT_COMMANDS:
            self.font_form.add(c)
        self.font_form.load()
        # 修改 Fonts（如 ComboPrefix / ScorePrefix）实时刷新预览
        self.font_form.on_change = self._refresh_preview

        self.mania_editor = ManiaEditor(sub, self.ini,
                                         skin_folder_getter=lambda: self.skin_folder)
        sub.add(self.mania_editor, text="Mania")
        self.mania_editor.on_change = self._refresh_preview

    def jump_to_ini_for(self, element_name: str) -> None:
        """双击元素管理中的项时，切换到 skin.ini 编辑页最可能相关的子标签。

        目前仅做粗粒度跳转：mania 相关 -> Mania，字体/数字 -> Fonts，
        其余 -> General。精确滚动到字段需要额外维护映射表，后续可扩展。
        """
        name = element_name.lower()
        self.notebook.select(self.ini_tab)
        if name.startswith("mania-") or name.startswith("hit") or "combo" in name:
            self.ini_sub.select(self.mania_editor)
        elif any(x in name for x in ("score", "combo", "default", "hitcircle")):
            self.ini_sub.select(self.font_frame)
        else:
            self.ini_sub.select(self.gen_frame)

    # -- 动作 ------------------------------------------------------------
    def open_skin_folder(self):
        """在文件资源管理器中打开当前皮肤文件夹。"""
        if not getattr(self, "skin_folder", None):
            messagebox.showinfo("提示", "请先打开皮肤文件夹")
            return
        try:
            os.startfile(self.skin_folder)
        except Exception as exc:
            messagebox.showerror("无法打开文件夹", str(exc))

    def open_skin(self):
        folder = filedialog.askdirectory(title="选择皮肤文件夹")
        if not folder:
            return
        self._open_skin_path(folder)

    def _load_ini(self):
        path = os.path.join(self.skin_folder, "skin.ini")
        if os.path.exists(path):
            try:
                self.ini_encoding = detect_encoding(path)
                self.ini = SkinIni.parse(read_text_file(path))
            except Exception as exc:
                messagebox.showerror("读取失败", str(exc))
                self.ini_encoding = "utf-8-sig"
                self.ini = SkinIni()
        else:
            self.ini_encoding = "utf-8-sig"
            self.ini = SkinIni()
        self.stage_preview.clear_img_cache()
        self._reload_forms()

    def _reload_forms(self):
        self.general_form.getter = lambda k: self.ini.get("General", k)
        self.general_form.setter = lambda k, v: self.ini.set("General", k, v)
        self.general_form.load()
        self.colour_form.getter = lambda k: self.ini.get("Colours", k)
        self.colour_form.setter = lambda k, v: self.ini.set("Colours", k, v)
        self.colour_form.load()
        self.font_form.getter = lambda k: self.ini.get("Fonts", k)
        self.font_form.setter = lambda k, v: self.ini.set("Fonts", k, v)
        self.font_form.load()
        # 重建 mania 编辑器以重新绑定 ini
        self.mania_editor.ini = self.ini
        self.mania_editor.keys_var.set("4")
        self.mania_editor.reload()
        self.element_panel.refresh()
        self.stage_preview.refresh()

    def save_ini(self):
        if not self.skin_folder:
            messagebox.showinfo("提示", "请先打开一个皮肤文件夹")
            return
        self.general_form.save()
        self.colour_form.save()
        self.font_form.save()
        self.mania_editor.save()
        path = os.path.join(self.skin_folder, "skin.ini")
        text = self.ini.serialize()
        # 用读取时检测到的编码写回，避免中文乱码；无 BOM 的 UTF-8
        # 升级为带 BOM（utf-8-sig），否则记事本会按 ANSI 误读成乱码。
        enc = getattr(self, "ini_encoding", "utf-8-sig")
        if enc == "utf-8":
            enc = "utf-8-sig"
        if enc == "latin-1":
            # latin-1 是读取兜底编码，无法写回新增的中文，改用 UTF-8
            enc = "utf-8-sig"
        # 原子写入：先写临时文件再替换，编码失败或中途出错时
        # 原 skin.ini 保持完好，绝不会被清空。
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding=enc, newline="") as f:
                f.write(text)
            os.replace(tmp, path)
        except Exception as exc:
            try:
                os.remove(tmp)
            except OSError:
                pass
            messagebox.showerror("保存失败", str(exc))
            return
        messagebox.showinfo("已保存", f"skin.ini 已保存到\n{path}")

    def new_skin(self):
        parent = filedialog.askdirectory(title="选择新建皮肤的父文件夹")
        if not parent:
            return
        name = simpledialog.askstring("皮肤名称", "请输入皮肤名称：", initialvalue="My Skin")
        if not name:
            return
        folder = os.path.join(parent, name)
        try:
            os.makedirs(folder, exist_ok=True)
        except OSError as exc:
            messagebox.showerror("创建失败", str(exc))
            return
        ini_path = os.path.join(folder, "skin.ini")
        if os.path.exists(ini_path) and not messagebox.askyesno(
                "确认", "该文件夹已存在 skin.ini，是否覆盖？"):
            return

        self.skin_folder = folder
        self.path_var.set(folder)
        self.manager = SkinManager(folder)
        self.ini = SkinIni()
        self.ini.set("General", "Name", name)
        self.ini.set("General", "Version", "latest")
        sec = Section(name="Mania")
        sec.set("Keys", "4")
        self.ini.sections.append(sec)
        try:
            self.ini_encoding = "utf-8-sig"
            with open(ini_path, "w", encoding=self.ini_encoding) as f:
                f.write(self.ini.serialize())
        except OSError as exc:
            messagebox.showerror("保存失败", str(exc))
            return
        self._load_ini()
        self.settings["last_skin"] = folder
        save_settings(self.settings)
        messagebox.showinfo("创建成功", f"皮肤已创建：\n{folder}")

    def _bind_notebook_change(self):
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _on_tab_changed(self, event):
        self.stage_preview.refresh()

    def _refresh_preview(self):
        self.stage_preview.refresh()


def run():
    enable_dpi_awareness()
    app = App()
    app._restore_last_skin()
    app.mainloop()


if __name__ == "__main__":
    run()
