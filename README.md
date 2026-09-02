# OsuSkinMaker v0.0.4

一个集 **游玩预览**、**元素管理**、**skin.ini 编辑**于一体的 osu! mania 皮肤制作 GUI 工具。

**使用的话要备份皮肤文件，备份，备份，备份！！！**
<img width="853" height="504" alt="image" src="https://github.com/user-attachments/assets/939e8e58-f2cd-452a-a250-6234379b2ffa" />

---

## 目录

### 使用说明
- [启动](#启动)
- [工具栏](#工具栏)
- [设置弹窗](#设置弹窗)
- [记忆功能](#记忆功能)
- [素材文件编码与保存安全](#素材文件编码与保存安全)
- [左侧：游玩预览](#左侧游玩预览)
- [右侧：元素管理](#右侧元素管理)
- [右侧：skin.ini 编辑](#右侧skinini-编辑)
- [注意事项](#注意事项)
- [悄悄话](#悄悄话)

### 项目结构
- [文件总览](#文件总览)
- [依赖关系](#依赖关系)
- [辅助文件说明](#辅助文件说明)
- [1. main.py — 入口](#1-mainpy--入口)
- [2. catalog.py — 元素目录](#2-catalogpy--元素目录)
- [3. skin_ini.py — skin.ini 引擎](#3-skininipy--skinini-引擎)
- [4. manager.py — 皮肤文件扫描](#4-managerpy--皮肤文件扫描)
- [5. theme.py — 主题样式](#5-themepy--主题样式)
- [6. app_settings.py — 应用设置持久化](#6-appsettingspy--应用设置持久化)
- [7. utilities.py — 通用纯函数](#7-utilitiespy--通用纯函数)
- [8. components.py — 可复用 UI 组件](#8-componentspy--可复用-ui-组件)
- [9. gui.py — 主界面](#9-guipy--主界面)
- [如何添加新功能](#如何添加新功能)
- [预览自定义数值与显示开关](#预览自定义数值与显示开关)

---

# 使用说明

## 启动

```bash
cd e:\trae\osuskin
python main.py
```

> 也可运行 `build_exe.bat` 打包成 `dist\OsuSkinMaker.exe` 后双击运行（无需 Python 环境）。
>
> 或者点击run.bat

启动后自动恢复上次退出时的窗口大小/位置与面板比例，并自动打开上次编辑的皮肤。

左侧为**游玩预览**，右侧为**元素管理**和**skin.ini 编辑**，可拖动中间分隔条调整比例。

---

## 工具栏

| 按钮 | 说明 |
|------|------|
| 打开皮肤 | 选择一个皮肤文件夹，自动加载里面的图片和 skin.ini |
| 新建 | 在指定父目录下创建新的皮肤文件夹，自动生成 skin.ini 模板 |
| 保存 | 将当前修改写回 skin.ini 文件（保留原编码，中文不乱码） |
| 文件夹 | 在文件资源管理器中打开当前皮肤文件夹 |
| 设置 | 打开设置弹窗（含浅色/深色主题切换，可自由缩放、右侧带滚动条） |
| 右侧卡片 | 显示当前皮肤文件夹路径 |

## 设置弹窗

- **主题**：浅色 / 深色切换
- **编辑方式**：点击"浏览"选择素材后的处理方式
  - **直接导入路径**（原方式）：把素材在皮肤内的相对路径写入 skin.ini
  - **复制到文件夹**：把素材复制到皮肤根目录下的目标文件夹（默认 `mania`，可自定义），再写入"文件夹名/文件名"相对路径；文件已在目标位置时跳过复制，同名冲突时询问是否覆盖
- **导入素材**：添加/替换组件时对 @2x 的默认处理（@2x / 原图 / 每次自行确认）
- **游玩预览**：缺失的组件是否显示默认组件
  - 开启：舞台、按键、音符、判定等组件缺失时以默认样式显示
  - 关闭：则不显示这些缺失组件（连击图为可选装饰，缺失时一直不绘制）
- **点击选中游玩预览组件**：开启后可在预览画面直接点击选中某个组件，右侧元素管理会联动选中对应的元素；单击选中最上层，双击切换到被遮挡的下一层（循环）
- **元素管理按当前预览界面分类显示**（默认开启）：
  - 开启：元素面板只显示当前界面（游玩/暂停/失败/结算/选歌）的元素 + 所有界面通用的元素
  - 关闭：任意界面都显示全部元素（仍保持树状分组结构，不改变分类，只是展示全部）
- 弹窗支持自由缩放，内容超出时右侧出现滚动条（滚轮滚动）

## 记忆功能

程序把以下内容记录到 **`settings/` 文件夹**下的 `settings.json`（exe 版记录在 exe 同目录），下次启动自动恢复：

- 上次编辑的皮肤文件夹（打开/新建时记录）
- 主题、编辑方式、导入 @2x 策略、缺失组件默认显示开关、点击选中预览组件开关、"按当前预览界面分类显示"开关
- 窗口大小/位置/最大化状态，以及主窗口、元素管理面板的分隔条比例
- **元素管理**：分类树的展开/收缩状态（切换界面、导入/替换组件、重启后都会保持，仅记住你手动展开的那一层）
- **预览状态**：最后一次的界面（游玩界面 / 暂停界面 / 失败界面 / 成绩结算界面 / 选歌界面）、显示开关（背景图/连击图/警告箭头/跳过按钮）、画幅比例、自定义分数/acc/连击/中间评分

## 素材文件编码与保存安全

- 打开皮肤时自动检测 skin.ini 的编码（UTF-8 / UTF-8 BOM / GBK），保存时按原编码写回，中文不会变乱码
- 保存采用**原子写入**（先写临时文件再替换）：即使保存失败，原 skin.ini 也不会被清空或损坏

---

## 左侧：游玩预览

### 控制栏
- **界面**：下拉选择预览的界面
  - **游玩界面**：正常游玩画面
  - **暂停界面**：压暗游玩画面 + 覆盖层 + 三个按钮，右侧元素管理同步只显示 `pause-*` 相关元素
  - **失败界面**：独立的失败界面（fail-background 铺满 + 重试/返回两个按钮，不绘制游玩画面）
  - **成绩结算界面 / 选歌界面**：下拉中可选中，但画面切换尚未实现（选中后画面不变，仅元素筛选可受其影响）
  
  **比例**：16:9 / 16:10 切换
  
- **显示**：弹出小窗，勾选预览中是否显示背景图（menu-background）、连击图（comboburst）、警告箭头（mania-warningarrow）、跳过按钮（play-skip）

- **数值**：弹出对话框，自定义预览中显示的分数、准确度、连击数、中间评分
  - 中间评分为下拉选择（300g / 300 / 200 / 100 / 50 / miss），对应切换对应的 hitburst 图片
  
- **刷新**：手动刷新预览

### 预览内容
预览基于 skin.ini 的 `[Mania]` 区块实时渲染（图层顺序与官方 mania 一致）：

- 列底、列分隔线、判定线
- 舞台灯光、左右边框、底部装饰
- 接收器（按键）、音符、灯光命中特效（lightingN/L）
- 连击图（comboburst）
- 游玩界面右下角的「跳过」按钮（play-skip，BottomRight 定位、乘法混合，可由"显示"开关控制）
- **HUD**：分数（8 位数）、准确度、连击计数、判定评分
- 血条（旋转 90°、0.7 缩放、贴底右对齐）

修改右侧 skin.ini 编辑器的任何字段，预览会**实时刷新**。

### 点击选中预览组件
在"设置"里开启"点击选中游玩预览组件"后：
- **单击**：选中点击位置最上层的组件，右侧元素管理联动选中对应元素
- **双击**：选中被最上层遮挡的下一层组件（如被舞台底部盖住的音符），继续双击逐层向下，到底后循环回顶层
- 在暂停界面下点击 overlay/按钮时，界面会保持暂停界面不动，正常选中对应的暂停元素

---

## 右侧：元素管理

### 筛选按钮
- **全部**：显示所有元素
- **缺失**：仅显示皮肤中不存在的元素
- **@2x**：仅显示有高清素材的元素
- **动画**：仅显示含帧动画的元素

### 状态颜色
- 绿色：存在
- 蓝色：存在（@2x）
- 红色：缺失
- 橙色：含动画帧

### 双击元素
双击存在元素，自动跳转到文件夹并选中该元素

双击缺失元素，自动跳转到skin.ini中

### 右侧预览区
点击元素可查看详细信息（描述、建议尺寸、混合模式、原点）和图片预览。

**图片预览交互**：
- **滚轮**：放大 / 缩小（以鼠标指针为中心），范围 5% ~ 2000%
- **左键拖动**：平移查看图片细节
- 选中新元素时自动适配画布并居中显示

### 素材操作
选中元素后，预览区下方出现操作按钮：

| 元素状态 | 按钮 | 功能 |
|---------|------|------|
| 缺失 | 添加素材 | 从皮肤文件夹中选择图片，复制到根目录并按元素名命名，可选择是否加 @2x |
| 存在 | 删除素材 | 确认后删除该元素的所有文件（含 @2x、动画帧） |
| 存在 | 替换素材 | 选择新图片，先复制新文件、再删除旧文件并以元素名命名（询问是否 @2x；不会误删源文件） |
| 多帧动画 | 播放动画 | 循环播放各帧动画 |

> 素材添加/替换时会写入 `文件名@2x.png`（如选择 @2x），与 osu! 官方规则一致。

---

## 右侧：skin.ini 编辑

### 子标签
- **General**：皮肤名称、作者、版本、动画帧率、光标行为等
- **Colours**：所有颜色（连击色、滑条色、菜单色等）
- **Fonts**：数字前缀（ScorePrefix、ComboPrefix）、间距（Overlap）
- **Mania**：键数（1~18K）、列宽、判定线高度、长条身体样式、连击位置、倒置、每列 KeyImage/NoteImage 等

### 字段操作
- 直接修改输入框，修改实时生效并刷新预览
- **↺ 按钮**：将单个字段恢复为 skin.ini 文件中的原始值（非 schema 默认值）
- **"重置所有"按钮**（Mania 标签）：重新从 skin.ini 加载所有字段
- **浏览按钮**（仅图片路径字段，如 StageLeft、KeyImage 等）：按设置中的"编辑方式"处理——直接导入路径模式：选择皮肤内的图片，把相对路径写入字段（不写 @2x 后缀）；复制到文件夹模式：把图片复制到皮肤下指定文件夹再写入路径

### 颜色字段
- 输入框旁有色板预览
- 点"选色"按钮可打开系统取色器

### 数值字段
- 输入框旁有滑块辅助调整（范围 0~1000）

### 下拉字段（choice，如长条身体样式）
- 界面显示中文标签（如 `0=拉伸`、`1=从顶`、`2=从底`）
- 保存到 skin.ini 时自动写入**纯枚举值**（`0/1/2`），osu! 能正确读取

---

## 注意事项

- 预览中的坐标系统基于 **x480**（游戏区域高度 480 单位）
- HUD 元素（分数、acc、连击、血条、hitburst）在官方 x768 基准中显示，预览中已自动 ÷1.6 换算
- 左右舞台（mania-stage-left/right）按官方规则**垂直拉伸**到舞台高度、宽度保持原比例（x768 基准 ÷1.6 换算），非等比缩放
- 舞台底部（mania-stage-bottom）按 480px 基准等比显示，不拉伸
- @2x 素材在打开时自动缩放到 1x 逻辑尺寸
- 素材读取优先级与 osu! 基本官方一致：skin.ini 指定路径（@2x → 原版）→ 默认文件名（@2x → 原版）
- 多帧动画元素默认显示第一帧
- **长条身体样式**：`0=拉伸`（单图拉伸）、`1=从顶`（按贴图顶部平铺）、`2=从底`（按贴图底部平铺，顶端不留透明空隙）
- 明暗主题切换会保留所有已打开皮肤与当前编辑状态
- **暂停界面**：切换时先把游玩画面压暗约 70%，再叠加 `pause-overlay`（不拉伸、按原生尺寸 ÷1.6 居中）与三个按钮（继续/重试/返回，SD 纵坐标 224/400/576 → x480 的 140/250/360）
- 界面类型、显示开关、画幅比例与自定义数值都会在退出时记录，下次启动自动恢复
- 预览里的坐标、尺寸、图层顺序都尽量贴近 osu! 官方规范，但**预览 ≠ 实机**。

---

## 悄悄话

2026.8.28

- 一个很糙的ai生成的小玩意QWQ（主要是用了dsv4flash）。可能优化不是很好，还有一堆神秘bug，ui也丑
- 一旁的组件也没有仔细的分类，而且，目前还只有mania的skin.ini编辑功能和展示。我对其他模式不太了解，所以就没有弄出来
- 选歌界面的预览和成绩结算的预览没有搞出来，这些组件的摆放有点难搞，如果之后有时间的话就弄一下。估计也没什么时间了，如果有大佬接力的话万分感谢。
- 如果有什么建议的话也欢迎提出，谢谢各位

---

# 项目结构

## 文件总览

```
e:\trae\osuskin\
├── main.py              入口（仅调用 gui.run()）
├── gui.py               主界面（界面层，约 3150 行）
├── components.py        可复用 UI 组件（滚动容器、颜色工具、字体后缀）
├── theme.py             主题样式（配色表 + setup_style + DPI）
├── app_settings.py      应用设置持久化（settings.json 读写与迁移）
├── utilities.py         通用纯函数（编码/颜色/数值解析）
├── skin_ini.py          skin.ini 解析 + 命令 schema（数据层）
├── catalog.py           元素目录（数据层，只读）
├── manager.py           皮肤文件扫描（业务层）
├── requirements.txt     依赖清单（Pillow）
├── build_exe.bat        打包成 exe 的脚本
├── run.bat              一键启动脚本（自动建 .venv、装依赖并运行）
├── osu_skin_tool.spec    PyInstaller 打包配置
├── README.md            本文件（使用说明 + 开发者修改指南）
└── .gitignore           git 忽略规则
```
另有不入版本库的目录（均在 `.gitignore` 中忽略）：
- `settings/`：应用设置（`settings.json`，exe 版写在 exe 同目录）
- `temp/`：临时文件（查询核对脚本、缓存等）
- `.venv/`：本地虚拟环境
- `build/`、`dist/`：PyInstaller 中间产物与打包输出

## 依赖关系

```
gui.py ──► skin_ini.py  catalog.py  manager.py   （数据/业务层）
   │          │            │            │
   ├──► theme.py ──────────┴────────────┘
   ├──► app_settings.py
   ├──► utilities.py ──► components.py
   └────────────────────────────┘
```

- `theme / app_settings / utilities / components` 为**工具/界面辅助层**，无本项目内部依赖，改动最安全。
- `components` 依赖 `utilities`（颜色/数值工具）；`gui` 依赖以上全部 + 数据层。
- `Form` 虽为通用组件，但与 `ManiaEditor/App` 深度耦合，故保留在 `gui.py`。

---

## 辅助文件说明

### requirements.txt

```
Pillow>=9.0
```

项目唯一的第三方依赖。安装方式：

```bash
pip install -r requirements.txt
```

### build_exe.bat

一键打包脚本，将项目打包为单个 `dist\OsuSkinMaker.exe` 文件。执行步骤：

1. 检查 `.venv` 虚拟环境是否存在，不存在则自动创建
2. 安装 Pillow + PyInstaller
3. 用 PyInstaller 按 `osu_skin_tool.spec` 配置打包
4. 输出到 `dist\OsuSkinMaker.exe`

> 新拆分的模块（theme/components/app_settings/utilities）会被 gui.py 自动 import，PyInstaller 会一并打包，无需改 spec。

### run.bat

一键启动脚本（Windows）：自动检查/创建 `.venv` 虚拟环境、安装 `requirements.txt` 依赖，然后用 `pythonw`（无黑框）启动 `main.py`。

### osu_skin_tool.spec

PyInstaller 打包配置文件，关键参数：
- `console=False`：打包为窗口程序，不弹出命令行黑框
- `excludes`：排除 unittest、pydoc 等无需打包的模块以减小体积
- 输出文件名：`OsuSkinMaker.exe`

---

## 1. main.py — 入口

```python
from gui import run
if __name__ == "__main__":
    run()
```

**无需修改。** 分离入口是为了让 `gui.py` 可以被 PyInstaller 打包时直接 import。

---

## 2. catalog.py — 元素目录

**作用**：定义所有 osu! 皮肤元素的中文描述、模式分组与界面归属元数据。

### 关键结构

```python
class Element:
    filename: str       # 基础文件名，如 "mania-hit300g"
    category: str       # 功能分类，如 "判定 (Judgement)"（组内唯一）
    description: str    # 中文说明
    group: str          # 模式分组（一级树），如 "osu!mania" / "通用元素"
    animatable: bool    # 是否支持帧动画
    size: str           # 建议尺寸
    blend: str          # 混合模式
    origin: str         # 原点
    screens: tuple      # 所属界面，如 ("游玩",)；含 "通用" 则所有界面都显示
```

### 分类体系（两级树）

元素按 **模式分组 → 功能分类** 两级组织，`GROUPS` 字典定义分组的顺序与各自的分类列表：

| 分组 | 功能分类 |
|------|---------|
| 通用元素 | 光标 (Cursor)、游玩界面 (Play)、倒计时 (Countdown)、按钮 (Button)、主菜单 (Menu)、暂停界面 (Pause)、失败界面 (Fail)、结算 (Ranking)、输入覆盖层 (Input Overlay)、分数与准确度 (Score & Acc)、血条 (Scorebar) |
| 选歌元素 | 游戏模式图标 (Mode Icon)、选歌界面 UI (Song Select)、模组图标 (Mod Icon)、结算等级 (Rank Small) |
| osu!（标准） | 连击 (Comboburst)、打击圈 (Hitcircle)、打击判定 (Hitburst)、滑条 (Slider)、转盘 (Spinner)、粒子 (Particle)、灯光 (Lighting) |
| osu!mania | 音符 (Note)、长条头 (Hold Head)、长条身 (Hold Body)、长条尾 (Hold Tail)、按键 (Key)、判定 (Judgement)、舞台 (Stage)、灯光 (Lighting)、连击 (Comboburst)、其它 (Other) |
| osu!taiko（太鼓） | 太鼓区域 (Arena)、音符 (Note)、滚打 (Roll)、摇器 (Spinner)、太鼓小人 (Pippidon)、打击结果 (Hit)、游玩区域 (Field) |
| osu!catch（接水果） | 水果 (Fruit)、连击 (Comboburst) |

### 界面过滤（screens）

元素面板按当前预览界面过滤元素：每个元素通过 `screens` 字段标注所属界面（游玩/暂停/失败/结算/选歌），含 `"通用"` 的元素在所有界面都显示。页面下拉值 → 界面名映射在 `PAGE_SCREEN` 中定义。

### 如何添加新元素

在 `ELEMENTS` 列表末尾追加一行：

```python
Element("新文件名", "分类名", "中文说明", True/False, "", "Normal", "Centre"),
```

若元素只属于某个特定界面，追加 `screens=("界面名",)`；若所有界面都显示，追加 `screens=("通用",)`。

### 如何修改分类

在 `GROUPS` 字典调整分组顺序或增删分类名，然后把 `ELEMENTS` 中对应元素的 `category`（以及需要时 `group`）改为新值。

### 工具函数

- `by_group()` → `{分组: {分类: [Element, ...]}}`，两级嵌套结构（GUI 元素面板按此渲染三级树）
- `by_category()` → `{分类名: [Element, ...]}`（兼容旧接口）
- `by_name(filename)` → 按文件名查找 Element

---

## 3. skin_ini.py — skin.ini 引擎

### 数据模型

| 类 | 说明 |
|----|------|
| `Entry` | 一条记录：`key`（命令名）、`value`（值）、`is_comment`（是否注释） |
| `Section` | 一个 `[区块]`，包含多个 Entry |
| `SkinIni` | 整个文件，`sections` 列表 |

### 解析逻辑

`SkinIni.parse(text)`：逐行解析，支持：
- `//` 开头的注释；也剥离命令值**行尾**的 `//` 注释（如 `Keys: 4 //4K注释` 读为 `4`，防止带行尾注释的皮肤整段匹配不上）
- `键: 值` 命令
- 同名多区块（如多个 `[Mania]`，每个不同键数）
- 空行和无法识别的行保留为注释

### 序列化逻辑

`SkinIni.serialize()`：把内存对象写回文本，保留注释和空行。

### 命令 Schema（Command）

```python
class Command:
    key: str       # 命令名，如 "ColumnStart"
    type: str      # 渲染类型：text / image / int / number / bool / rgb / rgba
                   #           / list / choice / keys
    label: str     # 中文标签
    default: str   # 默认值
    choices: tuple # choice 类型的可选值
    help: str      # 提示文字
```

> `type="image"` 表示图片路径字段（StageLeft、KeyImage{n0} 等），表单渲染时会附带"浏览"按钮；普通 `text` 字段（皮肤名称、作者等）没有浏览按钮。

### 如何添加新命令

1. 找到对应区块的命令列表（如 `MANIA_COMMANDS`）
2. 追加一行：

```python
Command("命令名", "类型", "标签", "默认值", help="提示"),
```

3. 如果是每列命令（如 Colour{n1}），添加到 `MANIA_COLUMN_COMMANDS`，用 `{n0}` 或 `{n1}` 作为列号占位符

### 命令列表

| 变量 | 区块 | 内容 |
|------|------|------|
| `GENERAL_COMMANDS` | [General] | 名称、版本、动画帧率、光标行为等 |
| `COLOUR_COMMANDS` | [Colours] | 连击色、滑条色、菜单色等 |
| `FONT_COMMANDS` | [Fonts] | 前缀、Overlap 间距 |
| `MANIA_COMMANDS` | [Mania] | 键数、列宽、判定线、连击位置等 |
| `MANIA_COLUMN_COMMANDS` | [Mania] 每列 | Colour{n1}、KeyImage{n0}、NoteImage{n0} 等 |
| `NOTE_LAYOUT` | 字典 | 各键数对应的默认音符编号，覆盖 1~18K，如 `4: ["1","2","2","1"]` |

---

## 4. manager.py — 皮肤文件扫描

### 核心函数

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `strip_hd(stem)` | `"score-3@2x"` | `"score-3"` | 去掉 @2x/2x 后缀 |
| `parse_stem(stem)` | `"mania-note1-3@2x"` | `("mania-note1", True, 3)` | 解析文件名 |
| `is_hd_path(path)` | 文件路径 | True/False | 静态方法，判断是否 @2x |

### 核心类：SkinManager

```python
class SkinManager:
    def __init__(self, folder):
        # 三个索引：
        self._base_files = {}    # 基础名 -> {paths, hd, frames}
        self._stem_files = {}    # 含目录主干 -> [路径]（精确查找）
        self._stem_plain = {}    # 纯文件名 -> [路径]（宽松查找）
```

| 方法 | 说明 |
|------|------|
| `scan()` | 遍历文件夹所有图片，建立三个索引 |
| `path_for(base)` | 查找元素文件，@2x 优先，支持回退到 stem 模糊查找 |
| `path_for_exact(base)` | 同 path_for 但**不回退**到 stem 模糊查找（skin.ini 指定的路径专用） |
| `path_for_stem(stem)` | 精确查找（如 `score-3`、`score-percent`） |
| `status(element)` | 返回 ElementStatus（存在/高清/帧数） |
| `summary()` | 返回 `{total, present, missing}` 统计 |

### 文件查找优先级

1. 精确主干（含目录）→ 2. 纯文件名 → 3. 多个候选时 @2x 优先、动画帧 0 优先

### 素材读取优先级（与 osu! 官方一致）

路径查询统一走 `_resolve_path`，skin.ini 里指定的图片路径**带不带扩展名（如 `mania/key.png` 或 `mania/key`）都能命中**：

| 优先级 | 查找方式 |
|--------|---------|
| 1 | skin.ini 指定路径 → @2x 版本（精确匹配） |
| 2 | skin.ini 指定路径 → 原版 |
| 3 | 默认文件名 → @2x（可模糊回退） |
| 4 | 默认文件名 → 原版 |

多帧动画默认取第 0 帧（`hit300g-0@2x.png` > `hit300g-0.png` > `hit300g@2x.png` > ...）。

---

## 5. theme.py — 主题样式

**作用**：集中管理明暗主题配色与 ttk 样式，供整个界面复用。

| 符号 | 说明 |
|------|------|
| `THEMES` | 字典：`light`/`dark` 两套配色（bg/panel/text/accent 等键） |
| `current_theme()` | 返回当前主题名 `light/dark` |
| `theme_color(key)` | 取当前主题的某个颜色值（如 `theme_color("bg")`） |
| `enable_dpi_awareness()` | Windows 高 DPI 感知，避免高分屏模糊 |
| `setup_style(root, theme)` | 应用主题：设置全局字体、配置所有 ttk 控件样式（按钮/输入框/Notebook/Treeview 等） |

### 修改主题颜色

改 `THEMES` 字典中 `light` 和 `dark` 两组配色即可；新增某个控件的专属样式时在 `setup_style()` 中配置，注意明暗两套都要生效（用变量取值，不写死颜色）。

---

## 6. app_settings.py — 应用设置持久化

**作用**：读写 `settings/` 下的 `settings.json`。

| 函数 | 说明 |
|------|------|
| `_settings_path()` | 配置文件路径：`<基础目录>/settings/settings.json`（exe 时为 exe 同目录） |
| `load_settings()` | 读取配置；不存在时自动从旧位置（根目录 settings.json）迁移 |
| `save_settings(data)` | 原子写回，失败静默忽略 |

---

## 7. utilities.py — 通用纯函数

**作用**：与 tkinter 无关的纯函数，供各界面模块复用。

| 函数 | 说明 |
|------|------|
| `read_text_file(path)` | 按探测编码读取文本 |
| `detect_encoding(path)` | 探测文件编码：UTF-8(含BOM) → GBK → latin-1 兜底 |
| `parse_rgb(text)` | 解析 `'R,G,B'` 为 `(r,g,b)`，失败返回 None |
| `rgb_to_hex(rgb)` | `(r,g,b)` → `'#rrggbb'` |
| `_num(s, default)` | 转浮点，失败返回默认值 |
| `_choice(s, default)` | choice 字段值转数值，兼容 `'0=拉伸'` 标签与纯 `'0'` |
| `_num_list(s, default, count)` | 解析逗号分隔的数值列表 |

---

## 8. components.py — 可复用 UI 组件

**作用**：不依赖 skin.ini 逻辑的通用控件。

| 符号 | 说明 |
|------|------|
| `ScrollableFrame` | 带垂直滚动条 + 滚轮支持的容器 |
| `pick_color(var, swatch, has_alpha)` | 打开系统取色器并写回 RGB(A) 字符串 |
| `apply_swatch(swatch, text)` | 根据 RGB 字符串刷新色板背景色 |
| `FONT_SUFFIXES` | 数字字体后缀集合（0-9/percent/comma/dot/x），浏览选择字体时同组复制用 |

---

## 9. gui.py — 主界面

### 文件结构

| 行号 | 区域 | 说明 |
|------|------|------|
| 1-50 | 导入 | 标准库、tkinter、PIL（HAS_PIL）、各内部模块 |
| 51-339 | **`Form` 类** | 通用表单引擎 |
| 340-487 | **`ManiaEditor` 类** | Mania 编辑器（每列表单 + reset） |
| 488-1178 | **`ElementPanel` 类** | 元素管理面板（浏览/添加/删除/替换/预览） |
| 1179-2583 | **`StagePreview` 类** | 游玩/暂停/结算/选歌预览（最大模块） |
| 2584-3141 | **`App` 类** | 主窗口 |
| 3142 | `run()` | 程序入口（enable_dpi_awareness → setup_style → App.mainloop） |

> 行号随维护变动，以最新为准；下表用方法名定位更可靠。

### Form 类（表单引擎）

**作用**：根据 `Command` schema 自动渲染 GUI 控件，支持 load/save/重置。

**控件映射**：
| Command.type | 渲染控件 |
|-------------|---------|
| `text` | 文本框 |
| `image` | 文本框 + 浏览按钮（选皮肤内图片） |
| `int` / `number` | 文本框 + 滑块 |
| `bool` | 复选框 |
| `rgb` / `rgba` | 文本框 + 色板 + 选色按钮 |
| `choice` | 下拉框 |

**关键属性**：
```python
self.vars          # {key: tk.Variable}  所有控件的变量
self._originals    # {key: 原始值}       load() 时记录的 skin.ini 原始值
self.on_change     # 回调函数            字段变化时触发（实时预览）
self._loading      # 布尔值              load() 期间不触发回调
```

**关键方法**：
- `add(cmd)` — 渲染一个字段
- `load()` — 从 skin.ini 读取值填充控件，同时记录原始值
- `save()` — 将控件值写回 skin.ini
- `_reset_key(key)` — ↺ 按钮：恢复为原始值
- `_on_key_change(key)` — 字段变化：提交 ini + 触发预览刷新
- `_value_for_key(key, text)` — 控件文本 → 存 ini 的枚举值（choice 取 `=` 前）
- `_text_for_key(key, value)` — ini 值 → 控件显示标签（choice 取 `=` 后）
- `_browse_file(var)` — 浏览按钮：按设置中的"编辑方式"处理
  - `path` 模式（默认）：选皮肤内图片，写相对路径（自动去 @2x 后缀）
  - `copy` 模式：把图片复制到皮肤根目录下的目标文件夹（默认 `mania`），写"文件夹名/文件名"路径；已在目标位置跳过复制、同名询问覆盖；选择数字字体（score/combo）时用 `FONT_SUFFIXES` 判定并同组复制

> **choice 字段取值约定**：skin.ini 中写入纯枚举值（`0/1/2`），界面显示标签（`0=拉伸` 等）。写文件走 `_value_for_key`，读显示走 `_text_for_key`，两者配套使用，勿直接用 `var.get()` 写文件（否则会把 `0=拉伸` 写入 skin.ini，osu! 报类型错误）。

### StagePreview 类（预览）

**坐标系**：x480，即游戏区域高度 480 单位，画布缩放系数 `scale = 画布高度 / 480`。

**HUD 换算**：HUD 元素（分数、acc、连击、血条、hitburst）在官方 x768 基准中显示，预览中 **÷1.6** 换算。`_draw_number` 的 `overlap` 参数也需 ÷1.6。

**关键方法**：
| 方法 | 行号 | 说明 |
|------|------|------|
| `_show_default_on` | 1294 | "缺失组件显示默认组件"开关状态 |
| `_resolve_path` | 1305 | 素材路径解析（skin.ini 指定路径优先；带不带扩展名均可命中） |
| `_draw_stage_side` | 1458 | 左右舞台：垂直拉伸到舞台高度、宽度保持原比例，x768 ÷1.6 |
| `_draw_stage_bottom` | 1487 | 底部装饰：480px 基准等比显示，不拉伸，绘制于左右舞台之上 |
| `_draw_play_skip` | 1772 | 游玩界面右下角「跳过」按钮（play-skip，BottomRight 定位、乘法混合） |

（其余通用方法的行号会随维护变动，建议用 grep 直接定位，不在此一一列举。）

**绘制顺序**（从底层到顶层，与官方 mania playfield 图层一致）：
1. 背景（menu-bg 或纯黑）
2. 血条、列底、列分隔线
3. 灯光（stage-light）
4. 接收器（按键）
5. 灯光命中特效（lightingN/L，官方位于音符下方的 Underlay 层）
6. 音符、长条（LN）
7. 判定线（stage-hint）
8. 警告箭头（warningarrow）
9. 左右舞台（stage-left/right，官方 StageForeground 层：覆盖音符，位于 HUD 之下）
10. 舞台底部装饰（stage-bottom，绘制于左右舞台之上以覆盖其边缘）
11. 连击图（comboburst）
12. **HUD**：分数 → acc → 连击计数 → 判定评分
13. 游玩界面右下角跳过按钮（play-skip，仅"游玩界面"界面绘制）

> 选中下拉"暂停界面"时，在游玩画面之上叠加：先压暗约 70% → `pause-overlay`（原生尺寸 ÷1.6 居中，不拉伸）→ 三个按钮（`pause-continue`/`pause-retry`/`pause-back`，SD 纵坐标 224/400/576 → x480 的 140/250/360）。

**性能优化**：
- `refresh()` 防抖：200ms 内多次刷新合并为一次（`_refresh_timer`）
- `_img_cache`：PIL 原图缓存，跨刷新复用（换肤时 `clear_img_cache()` 清理）
- `_photo_cache`：PhotoImage 缓存，以 `(img, w, h, flip)` 为键**跨刷新复用**，仅在换肤（`clear_img_cache`）时清空，避免每次改字段全量重建贴图导致卡顿
- 图片加载统一入口 `_open_skin_image()`，按文件 mtime 自动检测覆盖并重载

**NoteBodyStyle（长条身体样式）渲染**：
- `0=拉伸`：单张贴图拉伸填满
- `1=从顶`：按贴图顶部开始平铺
- `2=从底`：贴图底部对齐小头端向上平铺，顶端残片由画布截断、不留透明空隙
- 读取用 `_choice(vals.get("NoteBodyStyle"), 1)`，兼容标签文本与纯枚举值

**缺失组件占位**：由设置中"缺失组件显示默认组件"开关（`_show_default_on()`）控制。
- **开启**：舞台、按键、音符、判定评分等缺失时以默认样式占位显示（默认组件保持原样）
- **关闭**：这些缺失组件完全不绘制；连击图为可选装饰，缺失时一直不绘制占位

**页面切换与元素筛选**：`page_var`（预览上方下拉）驱动预览重绘与元素面板筛选——按当前界面只显示对应元素。该筛选由设置中"元素管理按当前预览界面分类显示"开关控制（关闭则显示全部元素）。

**点击联动选中**（设置中"点击选中游玩预览组件"开关开启时）：
- 渲染时给各组件画布项打 `pick:<元素名>` 标签
- 单击选中点击位置**最顶层**组件；双击选中被**下一层**遮挡的组件，循环切换
- 点击区域用 `find_overlapping` 命中（底层→顶层顺序），由 `_pick_stack`/`_pick_idx` 管理层级
- 暂停界面下点击联动**不切回游玩界面**（界面固定）
**预览状态持久化**：`_restore_preview_settings()` 启动时恢复上次退出时的界面类型、显示开关、画幅比例与自定义数值；`App._persist_settings()` 在关闭窗口时保存（`preview_page`/`preview_bg`/`preview_cb`/`preview_warning`/`preview_skip`/`preview_aspect`/`preview_score`/`preview_acc`/`preview_combo`/`preview_hit`）。元素面板展开/收缩状态由 `ElementPanel._save_open_state()` 保存到 `element_open_state`。

**倒置（UpsideDown）**：舞台坐标系 Y 镜像；按键/音符按 `KeyFlipWhenUpsideDown`/`NoteFlipWhenUpsideDown` 垂直翻转；左右舞台/底部图像**不翻转**，锚点适配（左右舞台锚视觉顶部、底部舞台锚 N 从顶悬挂）。

### ElementPanel 类（元素管理）

**素材操作**（选中元素后显示按钮）：
- `_add_asset(filename)` — 缺失元素：选图片复制到根目录，按元素名命名，询问是否 @2x
- `_delete_asset(filename, files)` — 删除该元素所有文件（含 @2x、动画帧）
- `_replace_asset(filename, files)` — 替换：先复制新文件、再删除旧文件（删除时跳过本次写出的目标路径，避免选中组件自身文件时源文件消失）
- 操作后统一 `_post_modify()` 刷新列表 + 预览 + 表单

**预览交互**：
- 常驻 Canvas（`_ensure_canvas`），换元素不销毁
- 滚轮缩放（`_zoom_at`）、左键拖动（`_on_pan_start`/`_on_pan_move`）
- 动画播放复用画布，换帧不重建、不居中跳动

### App 类（主窗口）

**布局**：
```
├── 工具栏（打开皮肤/新建/保存 | 文件夹 | 设置 | 主题切换 | 路径卡片）
└── PanedWindow（weight 5:1，可拖动，比例自动记忆恢复）
    ├── StagePreview（weight=5，占 5/6）
    └── Notebook（weight=1，占 1/6）
        ├── 元素管理
        └── skin.ini 编辑
            ├── General
            ├── Colours
            ├── Fonts
            └── Mania
```

**关键方法**：
- `open_skin()` — 打开皮肤文件夹
- `_load_ini()` — 解析 skin.ini（记录原编码 `ini_encoding`），重建所有表单
- `save_ini()` — 原子写入（临时文件 + os.replace），按原编码写回，UTF-8 自动带 BOM
- `new_skin()` — 创建新皮肤
- `open_skin_folder()` — 在资源管理器中打开皮肤文件夹
- `_toggle_theme()` — 切换明暗主题
- `_open_settings()` — 设置弹窗（可缩放 + 滚动条）：主题、编辑方式、导入 @2x 策略、缺失组件默认显示开关、点击选中预览组件开关
- `_persist_settings()` — 把当前设置写回 settings.json（含窗口 geometry、state、两个面板 sash 比例、预览状态）
- `_restore_window()` — 启动时恢复窗口大小/位置/最大化状态
- `_restore_sashes(attempt)` — 恢复主窗口/元素管理面板分隔条比例（相对比例换算 + 自动重试）
- `_restore_last_skin()` — 启动时自动打开上次编辑的皮肤
- `jump_to_ini_for(name)` — 双击元素跳转编辑页（粗粒度：mania → Mania，字体 → Fonts，其他 → General）
- `_refresh_preview()` — 刷新预览

### 编码处理（防止中文乱码）

| 函数（位于 utilities.py） | 说明 |
|------|------|
| `detect_encoding(path)` | 探测文件编码：UTF-8(含BOM) → GBK → latin-1 兜底 |
| `read_text_file(path)` | 按探测编码读取文本 |

`save_ini()`（gui.py）按原编码写回；无 BOM 的 UTF-8 升级为 utf-8-sig；latin-1 无法写中文时改用 utf-8-sig。

---

## 如何添加新功能

### 添加新的 skin.ini 字段

1. 在 `skin_ini.py` 对应命令列表加一行 `Command(...)`
2. 无需修改 Form 类—它会自动渲染对应控件
3. 若字段要影响预览，再在 `StagePreview._draw()` 中处理

### 修改预览中的绘制逻辑

修改 `StagePreview._draw()` 方法（gui.py）。

### 修改主题颜色

修改 `theme.py` 中 `THEMES` 字典的 `light` 和 `dark` 两组配色，以及 `setup_style()` 中的控件样式定义。

### 修改坐标换算规则

`StagePreview._draw()` 中的 `scale` 变量和 `X()`/`Y()` 函数控制所有坐标变换。

### 修改 HUD 元素尺寸

HUD 元素（分数、acc、连击、血条）的 size 计算中都有 `/ 1.6` 因子，位于 `_draw_number` / `_draw_scorebar`。左右舞台（`_draw_stage_side`）同样按 x768 基准 ÷1.6 后垂直拉伸。暂停界面按钮/覆盖层（`_draw_pause`）同样按 ÷1.6 换算。

### 修改元素目录

编辑 `catalog.py` 的 `ELEMENTS` 列表和 `GROUPS` 字典（后者是两级分组结构与顺序的唯一来源；`CATEGORIES` 由 `GROUPS` 派生，无需手改）。新增/调整界面归属用 `screens` 字段。

### 修改素材读取优先级

`gui.py` 的 `_resolve_path()` + `manager.py` 的 `path_for` / `path_for_exact` / `_first_hd`。注意：skin.ini 指定路径用精确（不回退），默认文件名可回退。

### 修改编码处理

`utilities.py` 的 `detect_encoding()` / `read_text_file()`；gui.py 的 `save_ini()`。规则：保存必须原子写入（临时文件 + `os.replace`），否则编码失败会清空原文件。

---

## 预览自定义数值与显示开关

"数值"对话框（`_open_value_dialog`）中的可选项：
- **分数**：自由文本，用 ScorePrefix 数字图渲染
- **准确度**：自由文本，高度 = 分数 × 0.6
- **连击数**：自由文本，用 ComboPrefix 数字图渲染
- **中间评分**：下拉选择（300g/300/200/100/50/miss），对应切换 hitburst 图片
  - 映射关系在 `StagePreview.HIT_LOOKUP` 字典中（`Hit300g/Hit300/...` 对应 skin.ini 的 `HIT_INI_KEYS` 命令）

"显示"对话框（`_open_show_dialog`）提供四个开关，控制预览中是否绘制：
- **背景图**（menu-background，`bg_var`）
- **连击图**（comboburst，`cb_var`）
- **警告箭头**（mania-warningarrow，`warning_var`）
- **跳过按钮**（play-skip，`skip_var`）

以上界面类型、显示开关、画幅比例与自定义数值都会随设置持久化，退出后下次启动自动恢复。
