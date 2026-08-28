"""osu! 皮肤元素目录（mania 为重点，另含各模式通用元素）。

数据来源：osu! 官方 wiki（Skinning）。
用于元素管理界面：按“模式分组 → 功能分类”两级展示、检测缺失、预览。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Element:
    filename: str        # 基础文件名（不含扩展名）
    category: str        # 功能分类（组内唯一，用于二级树）
    description: str     # 中文说明
    group: str = "通用元素"     # 模式分组（一级树）
    animatable: bool = False    # 是否支持 -{n} 帧动画
    size: str = ""               # 建议尺寸
    blend: str = "Normal"        # 混合模式
    origin: str = "Bottom"       # 原点
    screens: tuple = ("游玩",)   # 所属界面；含"通用"则所有界面都显示


# 页面下拉值 → 界面名映射（用于元素面板按界面过滤）
PAGE_SCREEN = {
    "游玩界面": None,          # None 表示游玩主界面：显示"游玩/通用"元素
    "暂停界面": "暂停",
    "失败界面": "失败",
    "成绩结算界面": "结算",
    "选歌界面": "选歌",
}


# 模式分组 → 功能分类（保持顺序）
GROUPS: dict = {
    "通用元素": [
        "光标 (Cursor)", "游玩界面 (Play)", "倒计时 (Countdown)", "按钮 (Button)",
        "主菜单 (Menu)", "暂停界面 (Pause)", "失败界面 (Fail)", "结算 (Ranking)",
        "输入覆盖层 (Input Overlay)", "分数与准确度 (Score & Acc)", "血条 (Scorebar)",
    ],
    "选歌元素": [
        "游戏模式图标 (Mode Icon)", "选歌界面 UI (Song Select)", "模组图标 (Mod Icon)",
        "结算等级 (Rank Small)",
    ],
    "osu!（标准）": [
        "连击 (Comboburst)", "打击圈 (Hitcircle)", "打击判定 (Hitburst)",
        "滑条 (Slider)", "转盘 (Spinner)", "粒子 (Particle)", "灯光 (Lighting)",
    ],
    "osu!mania": [
        "音符 (Note)", "长条头 (Hold Head)", "长条身 (Hold Body)", "长条尾 (Hold Tail)",
        "按键 (Key)", "判定 (Judgement)", "舞台 (Stage)", "灯光 (Lighting)",
        "连击 (Comboburst)", "其它 (Other)",
    ],
    "osu!taiko（太鼓）": [
        "太鼓区域 (Arena)", "音符 (Note)", "滚打 (Roll)", "摇器 (Spinner)",
        "太鼓小人 (Pippidon)", "打击结果 (Hit)", "游玩区域 (Field)",
    ],
    "osu!catch（接水果）": ["水果 (Fruit)", "连击 (Comboburst)"],
}

# 兼容旧接口：分类名平铺（保持顺序）
CATEGORIES: list = [c for cats in GROUPS.values() for c in cats]

ELEMENTS: list = [
    # ==================== 通用界面 ====================
    # 光标
    Element("cursor", "光标 (Cursor)", "光标主体"),
    Element("cursortrail", "光标 (Cursor)", "光标拖尾"),
    Element("cursormiddle", "光标 (Cursor)", "光标中心点（可选）"),
    Element("cursor-smoke", "光标 (Cursor)", "拉烟效果（按住拉烟键时显示）"),
    Element("cursor-ripple", "光标 (Cursor)", "光标波纹（按下左右击键时显示）",
            "通用元素", False, "", "Additive", "Centre"),
    # 游玩界面
    Element("play-skip", "游玩界面 (Play)", "游玩“跳过”按钮（休息段，拉伸贴边；可动画）",
            "通用元素", False, "", "Multiplicative", "BottomRight"),
    Element("arrow-pause", "游玩界面 (Play)", "暂停箭头（覆盖 play-warningarrow，v2.6+ 引入）",
            "通用元素", False, "", "Normal", "Centre"),
    Element("arrow-warning", "游玩界面 (Play)", "休息结束警告箭头（覆盖 play-warningarrow，v2.6+ 引入）",
            "通用元素", False, "", "Normal", "Centre"),
    Element("play-warningarrow", "游玩界面 (Play)", "警告箭头（旧版，v2.6+ 被 arrow-* 覆盖）",
            "通用元素", False, "", "Multiplicative", "Centre"),
    Element("play-unranked", "游玩界面 (Play)", "未上架标识（使用禁用分数提交的模组时显示）",
            "通用元素", False, "", "Multiplicative", "Centre"),
    Element("multi-skipped", "游玩界面 (Play)", "多人游戏跳过标识",
            "通用元素", False, "60x30", "Normal", "BottomRight"),
    Element("section-pass", "游玩界面 (Play)", "休息时段通过标识（血量 >50%）",
            "通用元素", False, "", "Normal", "Centre"),
    Element("section-fail", "游玩界面 (Play)", "休息时段失败标识（血量 <50%）",
            "通用元素", False, "", "Normal", "Centre"),
    Element("masking-border", "游玩界面 (Play)", "宽屏遮罩边框（4:3 谱面在宽屏上时使用）",
            "通用元素", False, "最大高度 768px", "Normal", "Right"),
    # 倒计时
    Element("count3", "倒计时 (Countdown)", "倒计时数字 3", "通用元素", False, "", "Normal", "Centre"),
    Element("count2", "倒计时 (Countdown)", "倒计时数字 2", "通用元素", False, "", "Normal", "Centre"),
    Element("count1", "倒计时 (Countdown)", "倒计时数字 1（v2.0+ 居中显示）", "通用元素", False, "", "Normal", "Centre"),
    Element("ready", "倒计时 (Countdown)", "倒计时准备“准备好了吗？”", "通用元素", False, "", "Normal", "Centre"),
    Element("go", "倒计时 (Countdown)", "倒计时开始“Go!”", "通用元素", False, "", "Normal", "Centre"),
    # 按钮
    Element("button-left", "按钮 (Button)", "按钮左侧组件",
            "通用元素", False, "", "Multiplicative", "TopRight", ("结算", "选歌")),
    Element("button-middle", "按钮 (Button)", "按钮中间组件（拉伸适应宽度）",
            "通用元素", False, "", "Multiplicative", "Top", ("结算", "选歌")),
    Element("button-right", "按钮 (Button)", "按钮右侧组件",
            "通用元素", False, "", "Multiplicative", "TopLeft", ("结算", "选歌")),
    # 主菜单
    Element("menu-background", "主菜单 (Menu)", "主菜单背景（.jpg）",
            screens=("结算",)),
    Element("welcome_text", "主菜单 (Menu)", "欢迎文字", screens=("结算", "选歌")),
    Element("menu-snow", "主菜单 (Menu)", "主菜单雪花", screens=("结算", "选歌")),
    # 暂停界面（覆盖在游玩画面之上；按钮 Center 锚在画面中心纵线上）
    Element("pause-overlay", "暂停界面 (Pause)", "暂停覆盖层（Center，覆盖整个画面）",
            "通用元素", False, "1366x768", "Normal", "Centre", ("暂停",)),
    Element("pause-continue", "暂停界面 (Pause)", "继续按钮（回到游戏，中心 y≈100）",
            "通用元素", False, "", "Normal", "Centre", ("暂停",)),
    Element("pause-retry", "暂停界面 (Pause)", "重试按钮（中心 y≈178）",
            "通用元素", False, "", "Normal", "Centre", ("暂停", "失败", "结算")),
    Element("pause-back", "暂停界面 (Pause)", "返回按钮（退出到主菜单，中心 y≈256）",
            "通用元素", False, "", "Normal", "Centre", ("暂停", "失败", "结算")),
    # 失败界面
    Element("fail-background", "失败界面 (Fail)", "失败界面背景（Center，覆盖整个画面）",
            "通用元素", False, "1366x768", "Normal", "Centre", ("失败",)),
    # 结算
    Element("ranking-xh", "结算 (Ranking)", "SS+ 判定（隐/闪）", screens=("结算",)),
    Element("ranking-x", "结算 (Ranking)", "SS 判定", screens=("结算",)),
    Element("ranking-sh", "结算 (Ranking)", "S+ 判定（隐/闪）", screens=("结算",)),
    Element("ranking-s", "结算 (Ranking)", "S 判定", screens=("结算",)),
    Element("ranking-a", "结算 (Ranking)", "A 判定", screens=("结算",)),
    Element("ranking-b", "结算 (Ranking)", "B 判定", screens=("结算",)),
    Element("ranking-c", "结算 (Ranking)", "C 判定", screens=("结算",)),
    Element("ranking-d", "结算 (Ranking)", "D 判定", screens=("结算",)),
    Element("ranking-replay", "结算 (Ranking)", "重播按键（旧版，v2.0+ 被 pause-replay 替代）", screens=("结算",)),
    Element("ranking-retry", "结算 (Ranking)", "重试按键（旧版）", screens=("结算",)),
    Element("pause-replay", "结算 (Ranking)", "结算界面回放按钮（v2.0+ 替代 ranking-replay）",
            "通用元素", False, "", "Normal", "Right", ("结算",)),
    Element("ranking-accuracy", "结算 (Ranking)", "结算准确率标签（v2.0+ 位置 291,480）",
            "通用元素", False, "", "Normal", "TopLeft", ("结算",)),
    Element("ranking-graph", "结算 (Ranking)", "结算图表背景（顶部左侧前 7 像素应透明）",
            "通用元素", False, "最小 308x148", "Normal", "TopLeft", ("结算",)),
    Element("ranking-maxcombo", "结算 (Ranking)", "结算最大连击标签（v2.0+ 位置 8,480）",
            "通用元素", False, "", "Normal", "TopLeft", ("结算",)),
    Element("ranking-panel", "结算 (Ranking)", "结算面板背景（v2.0+ 位置 0,102）",
            "通用元素", False, "最大高度 666px", "Normal", "TopLeft", ("结算",)),
    Element("ranking-perfect", "结算 (Ranking)", "全连 (Perfect) 标识（v2.0+ 位置 416,688）",
            "通用元素", False, "", "Normal", "Centre", ("结算",)),
    Element("ranking-title", "结算 (Ranking)", "结算标题（到右侧水平距离 32px）",
            "通用元素", False, "", "Normal", "TopRight", ("结算",)),
    Element("ranking-winner", "结算 (Ranking)", "多人游戏获胜者头像（仅用于多人游戏）",
            "通用元素", False, "200x214", "Normal", "TopLeft", ("结算",)),
    # 输入覆盖层
    Element("inputoverlay-background", "输入覆盖层 (Input Overlay)", "输入覆盖层背景（逆时针旋转 90 度放大显示）",
            "通用元素", False, "193x55", "Normal", "TopRight"),
    Element("inputoverlay-key", "输入覆盖层 (Input Overlay)", "输入覆盖层按键（按下时短暂缩小）",
            "通用元素", False, "43x46", "Multiplicative", "Centre"),
    # 分数与准确度（数字/标点，前缀默认 score，可在 [Fonts] 里改 ScorePrefix / ComboPrefix）
    Element("score-pp", "分数与准确度 (Score & Acc)", "pp 标识（lazer）",
            "通用元素", False, "", "Normal", "Centre", ("游玩", "结算", "选歌")),
    Element("scoreentry-0", "分数与准确度 (Score & Acc)", "按键计数数字 0",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-1", "分数与准确度 (Score & Acc)", "按键计数数字 1",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-2", "分数与准确度 (Score & Acc)", "按键计数数字 2",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-3", "分数与准确度 (Score & Acc)", "按键计数数字 3",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-4", "分数与准确度 (Score & Acc)", "按键计数数字 4",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-5", "分数与准确度 (Score & Acc)", "按键计数数字 5",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-6", "分数与准确度 (Score & Acc)", "按键计数数字 6",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-7", "分数与准确度 (Score & Acc)", "按键计数数字 7",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-8", "分数与准确度 (Score & Acc)", "按键计数数字 8",
            "通用元素", False, "", "Normal", "Centre"),
    Element("scoreentry-9", "分数与准确度 (Score & Acc)", "按键计数数字 9",
            "通用元素", False, "", "Normal", "Centre"),
    Element("score-0", "分数与准确度 (Score & Acc)", "数字 0", screens=("游玩", "结算", "选歌")),
    Element("score-1", "分数与准确度 (Score & Acc)", "数字 1", screens=("游玩", "结算", "选歌")),
    Element("score-2", "分数与准确度 (Score & Acc)", "数字 2", screens=("游玩", "结算", "选歌")),
    Element("score-3", "分数与准确度 (Score & Acc)", "数字 3", screens=("游玩", "结算", "选歌")),
    Element("score-4", "分数与准确度 (Score & Acc)", "数字 4", screens=("游玩", "结算", "选歌")),
    Element("score-5", "分数与准确度 (Score & Acc)", "数字 5", screens=("游玩", "结算", "选歌")),
    Element("score-6", "分数与准确度 (Score & Acc)", "数字 6", screens=("游玩", "结算", "选歌")),
    Element("score-7", "分数与准确度 (Score & Acc)", "数字 7", screens=("游玩", "结算", "选歌")),
    Element("score-8", "分数与准确度 (Score & Acc)", "数字 8", screens=("游玩", "结算", "选歌")),
    Element("score-9", "分数与准确度 (Score & Acc)", "数字 9", screens=("游玩", "结算", "选歌")),
    Element("score-comma", "分数与准确度 (Score & Acc)", "千位分隔符 ,", screens=("游玩", "结算", "选歌")),
    Element("score-dot", "分数与准确度 (Score & Acc)", "小数点 .", screens=("游玩", "结算", "选歌")),
    Element("score-percent", "分数与准确度 (Score & Acc)", "百分号 %", screens=("游玩", "结算", "选歌")),
    Element("score-x", "分数与准确度 (Score & Acc)", "连击乘号 ×", screens=("游玩", "结算", "选歌")),
    # 连击数字（前缀默认 combo，可在 [Fonts] 里改 ComboPrefix）
    Element("combo-0", "分数与准确度 (Score & Acc)", "连击数字 0", screens=("游玩", "结算", "选歌")),
    Element("combo-1", "分数与准确度 (Score & Acc)", "连击数字 1", screens=("游玩", "结算", "选歌")),
    Element("combo-2", "分数与准确度 (Score & Acc)", "连击数字 2", screens=("游玩", "结算", "选歌")),
    Element("combo-3", "分数与准确度 (Score & Acc)", "连击数字 3", screens=("游玩", "结算", "选歌")),
    Element("combo-4", "分数与准确度 (Score & Acc)", "连击数字 4", screens=("游玩", "结算", "选歌")),
    Element("combo-5", "分数与准确度 (Score & Acc)", "连击数字 5", screens=("游玩", "结算", "选歌")),
    Element("combo-6", "分数与准确度 (Score & Acc)", "连击数字 6", screens=("游玩", "结算", "选歌")),
    Element("combo-7", "分数与准确度 (Score & Acc)", "连击数字 7", screens=("游玩", "结算", "选歌")),
    Element("combo-8", "分数与准确度 (Score & Acc)", "连击数字 8", screens=("游玩", "结算", "选歌")),
    Element("combo-9", "分数与准确度 (Score & Acc)", "连击数字 9", screens=("游玩", "结算", "选歌")),
    Element("combo-comma", "分数与准确度 (Score & Acc)", "连击千位分隔符 ,", screens=("游玩", "结算", "选歌")),
    Element("combo-dot", "分数与准确度 (Score & Acc)", "连击小数点 .", screens=("游玩", "结算", "选歌")),
    Element("combo-percent", "分数与准确度 (Score & Acc)", "连击百分号 %", screens=("游玩", "结算", "选歌")),
    Element("combo-x", "分数与准确度 (Score & Acc)", "连击乘号 x", screens=("游玩", "结算", "选歌")),
    # 血条（mania 中垂直显示在场地右侧）
    Element("scorebar-bg", "血条 (Scorebar)", "分数条（HP 血量）背景", screens=("游玩", "结算", "选歌")),
    Element("scorebar-colour", "血条 (Scorebar)", "分数条颜色层（靠近危险区变黑变红）", screens=("游玩", "结算", "选歌")),
    Element("scorebar-marker", "血条 (Scorebar)", "分数条标记（覆盖 ki 系列）", screens=("游玩", "结算", "选歌")),
    Element("scorebar-ki", "血条 (Scorebar)", "分数条通过标记（旧版，可被 marker 覆盖）", screens=("游玩", "结算", "选歌")),
    Element("scorebar-kidanger", "血条 (Scorebar)", "分数条警告标记（旧版）", screens=("游玩", "结算", "选歌")),
    Element("scorebar-kidanger2", "血条 (Scorebar)", "分数条危急标记（旧版）", screens=("游玩", "结算", "选歌")),

    # ==================== 选歌界面 (Song Select) ====================
    # 游戏模式图标
    Element("mode-osu", "游戏模式图标 (Mode Icon)", "osu! 标准模式大图标（选歌界面中央闪烁）",
            "选歌元素", False, "256x256", "Additive", "Centre", ("选歌",)),
    Element("mode-osu-med", "游戏模式图标 (Mode Icon)", "osu! 标准模式中图标（模式选择下拉菜单）",
            "选歌元素", False, "128x128", "Normal", "Centre", ("选歌",)),
    Element("mode-osu-small", "游戏模式图标 (Mode Icon)", "osu! 标准模式小图标（选择按钮上）",
            "选歌元素", False, "32x32", "Additive", "Centre", ("选歌",)),
    Element("mode-taiko", "游戏模式图标 (Mode Icon)", "osu!taiko 模式大图标（选歌界面中央闪烁）",
            "选歌元素", False, "256x256", "Additive", "Centre", ("选歌",)),
    Element("mode-taiko-med", "游戏模式图标 (Mode Icon)", "osu!taiko 模式中图标（模式选择下拉菜单）",
            "选歌元素", False, "128x128", "Normal", "Centre", ("选歌",)),
    Element("mode-taiko-small", "游戏模式图标 (Mode Icon)", "osu!taiko 模式小图标（选择按钮上）",
            "选歌元素", False, "32x32", "Additive", "Centre", ("选歌",)),
    Element("mode-fruits", "游戏模式图标 (Mode Icon)", "osu!catch 模式大图标（选歌界面中央闪烁）",
            "选歌元素", False, "256x256", "Additive", "Centre", ("选歌",)),
    Element("mode-fruits-med", "游戏模式图标 (Mode Icon)", "osu!catch 模式中图标（模式选择下拉菜单）",
            "选歌元素", False, "128x128", "Normal", "Centre", ("选歌",)),
    Element("mode-fruits-small", "游戏模式图标 (Mode Icon)", "osu!catch 模式小图标（选择按钮上）",
            "选歌元素", False, "32x32", "Additive", "Centre", ("选歌",)),
    Element("mode-mania", "游戏模式图标 (Mode Icon)", "osu!mania 模式大图标（选歌界面中央闪烁）",
            "选歌元素", False, "256x256", "Additive", "Centre", ("选歌",)),
    Element("mode-mania-med", "游戏模式图标 (Mode Icon)", "osu!mania 模式中图标（模式选择下拉菜单）",
            "选歌元素", False, "128x128", "Normal", "Centre", ("选歌",)),
    Element("mode-mania-small", "游戏模式图标 (Mode Icon)", "osu!mania 模式小图标（选择按钮上）",
            "选歌元素", False, "32x32", "Additive", "Centre", ("选歌",)),
    # 选歌界面 UI
    Element("selection-mode", "选歌界面 UI (Song Select)", "模式选择按钮",
            "选歌元素", False, "92x90", "Normal", "BottomLeft", ("选歌",)),
    Element("selection-mods", "选歌界面 UI (Song Select)", "模组选择按钮",
            "选歌元素", False, "77x90", "Normal", "BottomLeft", ("选歌",)),
    Element("selection-options", "选歌界面 UI (Song Select)", "设置按钮",
            "选歌元素", False, "77x90", "Normal", "BottomLeft", ("选歌",)),
    Element("selection-random", "选歌界面 UI (Song Select)", "随机选择按钮",
            "选歌元素", False, "77x90", "Normal", "BottomLeft", ("选歌",)),
    Element("selection-tab", "选歌界面 UI (Song Select)", "标签页（显示 4~5 个）",
            "选歌元素", False, "142x24", "Multiplicative", "TopLeft", ("选歌",)),
    Element("star", "选歌界面 UI (Song Select)", "难度星星（v2.2+ 必要时缩小最后一个）",
            "选歌元素", False, "50x50", "Multiplicative", "Centre", ("选歌",)),
    Element("star2", "选歌界面 UI (Song Select)", "装饰星星（选歌飞行、光标、Kiai 时间等）",
            "选歌元素", False, "24x24", "Additive", "Centre", ("选歌",)),
    Element("songselect-bottom", "选歌界面 UI (Song Select)", "选歌界面底部（拉伸到屏幕宽度）",
            "选歌元素", False, "", "Normal", "BottomLeft", ("选歌",)),
    Element("songselect-top", "选歌界面 UI (Song Select)", "选歌界面顶部",
            "选歌元素", False, "", "Normal", "TopLeft", ("选歌",)),
    Element("menu-back", "选歌界面 UI (Song Select)", "返回按钮",
            "选歌元素", False, "200x214", "Normal", "BottomLeft", ("选歌",)),
    Element("menu-button-background", "选歌界面 UI (Song Select)", "按钮背景（分数板、难度按钮等多处使用）",
            "选歌元素", False, "最小 690x85", "Multiplicative", "BottomLeft", ("选歌",)),
    # 模组图标
    Element("selection-mod-easy", "模组图标 (Mod Icon)", "Easy（简单）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-nofail", "模组图标 (Mod Icon)", "NoFail（失败不结算）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-halftime", "模组图标 (Mod Icon)", "HalfTime（半速）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-hardrock", "模组图标 (Mod Icon)", "HardRock（加硬）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-suddendeath", "模组图标 (Mod Icon)", "SuddenDeath（一击必死）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-doubletime", "模组图标 (Mod Icon)", "DoubleTime（加速）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-nightcore", "模组图标 (Mod Icon)", "NightCore（夜核）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-hidden", "模组图标 (Mod Icon)", "Hidden（隐藏）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-flashlight", "模组图标 (Mod Icon)", "Flashlight（手电筒）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-relax", "模组图标 (Mod Icon)", "Relax（放松）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-relax2", "模组图标 (Mod Icon)", "Relax2（AUTO 自动）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-autoplay", "模组图标 (Mod Icon)", "Autoplay（自动播放）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-perfect", "模组图标 (Mod Icon)", "Perfect（完美）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-scorev2", "模组图标 (Mod Icon)", "ScoreV2（新计分）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-spunout", "模组图标 (Mod Icon)", "SpunOut（自动转盘）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-cinema", "模组图标 (Mod Icon)", "Cinema（影院）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-target", "模组图标 (Mod Icon)", "Target（目标，cuttingedge 专用）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-fadein", "模组图标 (Mod Icon)", "FadeIn（淡入，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key1", "模组图标 (Mod Icon)", "Key1（1K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key2", "模组图标 (Mod Icon)", "Key2（2K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key3", "模组图标 (Mod Icon)", "Key3（3K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key4", "模组图标 (Mod Icon)", "Key4（4K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key5", "模组图标 (Mod Icon)", "Key5（5K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key6", "模组图标 (Mod Icon)", "Key6（6K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key7", "模组图标 (Mod Icon)", "Key7（7K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key8", "模组图标 (Mod Icon)", "Key8（8K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-key9", "模组图标 (Mod Icon)", "Key9（9K，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-keycoop", "模组图标 (Mod Icon)", "KeyCoop（合作，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-mirror", "模组图标 (Mod Icon)", "Mirror（镜像，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    Element("selection-mod-random", "模组图标 (Mod Icon)", "Random（随机关卡拉，mania）模组图标",
            "选歌元素", False, "64x64", "Normal", "Centre", ("选歌",)),
    # 结算等级（选歌/休息用）
    Element("ranking-X-small", "结算等级 (Rank Small)", "SS+ 等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-XH-small", "结算等级 (Rank Small)", "SS（银色）等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-S-small", "结算等级 (Rank Small)", "S 等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-SH-small", "结算等级 (Rank Small)", "S（银色）等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-A-small", "结算等级 (Rank Small)", "A 等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-B-small", "结算等级 (Rank Small)", "B 等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-C-small", "结算等级 (Rank Small)", "C 等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),
    Element("ranking-D-small", "结算等级 (Rank Small)", "D 等级小图标",
            "选歌元素", False, "34x40", "Normal", "Centre", ("选歌",)),

    # ==================== osu!（标准） ====================
    # 连击
    Element("comboburst", "连击 (Comboburst)", "连击爆发图（osu! 标准模式，v2.3+ 各模式用专用版本）",
            "osu!（标准）", True, "", "Normal", "Centre"),
    # 打击圈
    Element("hitcircle", "打击圈 (Hitcircle)", "打击圈主体（点击前渐隐，点击时展开）",
            "osu!（标准）", False, "128x128", "Multiplicative", "Centre"),
    Element("hitcircleoverlay", "打击圈 (Hitcircle)", "打击圈外框（可在数字上方或下方）",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("hitcircleselect", "打击圈 (Hitcircle)", "编辑器中选中的打击圈",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("approachcircle", "打击圈 (Hitcircle)", "缩圈（用连击色着色，随时间缩小）",
            "osu!（标准）", False, "126x126", "Multiplicative", "Centre"),
    Element("followpoint", "打击圈 (Hitcircle)", "连接线箭头（应指向右方）",
            "osu!（标准）", True, "", "Normal", "Centre"),
    Element("default-0", "打击圈 (Hitcircle)", "打击圈默认数字 0",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-1", "打击圈 (Hitcircle)", "打击圈默认数字 1",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-2", "打击圈 (Hitcircle)", "打击圈默认数字 2",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-3", "打击圈 (Hitcircle)", "打击圈默认数字 3",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-4", "打击圈 (Hitcircle)", "打击圈默认数字 4",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-5", "打击圈 (Hitcircle)", "打击圈默认数字 5",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-6", "打击圈 (Hitcircle)", "打击圈默认数字 6",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-7", "打击圈 (Hitcircle)", "打击圈默认数字 7",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-8", "打击圈 (Hitcircle)", "打击圈默认数字 8",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("default-9", "打击圈 (Hitcircle)", "打击圈默认数字 9",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    # 打击判定
    Element("hit300", "打击判定 (Hitburst)", "300 判定", "osu!（标准）", True),
    Element("hit300g", "打击判定 (Hitburst)", "300g (Geki) 判定", "osu!（标准）", True),
    Element("hit300k", "打击判定 (Hitburst)", "300k (Katu) 判定（结算屏幕不显示）", "osu!（标准）", True),
    Element("hit100", "打击判定 (Hitburst)", "100 判定", "osu!（标准）", True),
    Element("hit100k", "打击判定 (Hitburst)", "100k (Katu) 判定", "osu!（标准）", True),
    Element("hit50", "打击判定 (Hitburst)", "50 判定", "osu!（标准）", True),
    Element("hit0", "打击判定 (Hitburst)", "Miss 判定", "osu!（标准）", True),
    # 滑条
    Element("sliderb", "滑条 (Slider)", "滑条球动画（sliderb0, sliderb1…）", "osu!（标准）", True),
    Element("sliderb-nd", "滑条 (Slider)", "滑条球黑底（默认球）", "osu!（标准）", False),
    Element("sliderb-spec", "滑条 (Slider)", "滑条球高光层（默认球）", "osu!（标准）", False),
    Element("sliderstartcircle", "滑条 (Slider)", "滑条起点圈（覆盖 hitcircle）",
            "osu!（标准）", False, "128x128", "Multiplicative", "Centre"),
    Element("sliderstartcircleoverlay", "滑条 (Slider)", "滑条起点圈外框（需配合起点圈）",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("sliderendcircle", "滑条 (Slider)", "滑条终点圈（覆盖 hitcircle）",
            "osu!（标准）", False, "128x128", "Multiplicative", "Centre"),
    Element("sliderendcircleoverlay", "滑条 (Slider)", "滑条终点圈外框（需配合终点圈）",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("sliderscorepoint", "滑条 (Slider)", "滑条点（也用于太鼓滚打点）",
            "osu!（标准）", False, "16x16", "Normal", "Centre"),
    Element("sliderfollowcircle", "滑条 (Slider)", "滑条跟随圈（收集滑条点时短暂扩大）", "osu!（标准）", True),
    Element("reversearrow", "滑条 (Slider)", "折返箭头",
            "osu!（标准）", False, "128x128", "Normal", "Centre"),
    Element("sliderendmiss", "滑条 (Slider)", "滑条末端失误标识（lazer）",
            "osu!（标准）", False, "", "Normal", "Centre"),
    Element("slidertickmiss", "滑条 (Slider)", "滑条点失误标识（lazer）",
            "osu!（标准）", False, "", "Normal", "Centre"),
    Element("sliderpoint10", "滑条 (Slider)", "滑条点（v1.0 旧版）",
            "osu!（标准）", False, "", "Normal", "Centre"),
    Element("sliderpoint30", "滑条 (Slider)", "滑条点（v1.0 旧版）",
            "osu!（标准）", False, "", "Normal", "Centre"),
    # 转盘（旧版 <2.0）
    Element("spinner-circle", "转盘 (Spinner)", "转盘圆圈（旧版 <2.0）", "osu!（标准）", False),
    Element("spinner-background", "转盘 (Spinner)", "转盘背景（旧版 <2.0）",
            "osu!（标准）", False, "1024x702", "Multiplicative", "Centre"),
    Element("spinner-metre", "转盘 (Spinner)", "转盘进度条（旧版 <2.0）", "osu!（标准）", False),
    Element("spinner-osu", "转盘 (Spinner)", "转盘标识（v1.0 旧版）", "osu!（标准）", False),
    # 转盘（新版 >=2.0）
    Element("spinner-top", "转盘 (Spinner)", "转盘顶层（旋转第二快，中间层）", "osu!（标准）", False),
    Element("spinner-bottom", "转盘 (Spinner)", "转盘底层（旋转最慢）", "osu!（标准）", False),
    Element("spinner-middle", "转盘 (Spinner)", "转盘中间层（随时间变红作时间指示）", "osu!（标准）", False),
    Element("spinner-middle2", "转盘 (Spinner)", "转盘中层（旋转最快，第二高层）", "osu!（标准）", False),
    Element("spinner-glow", "转盘 (Spinner)", "转盘光晕（青色着色，奖励分时闪白）",
            "osu!（标准）", False, "", "Additive", "Centre"),
    Element("spinner-approachcircle", "转盘 (Spinner)", "转盘缩圈（新版 >=2.0）",
            "osu!（标准）", False, "384x384", "Normal", "Centre"),
    Element("spinner-rpm", "转盘 (Spinner)", "转速显示器（RPM）",
            "osu!（标准）", False, "280x56", "Normal", "TopLeft"),
    Element("spinner-spin", "转盘 (Spinner)", "转盘旋转提示（开始时显示）", "osu!（标准）", False),
    Element("spinner-clear", "转盘 (Spinner)", "转盘完成标识（达成要求时显示）", "osu!（标准）", False),
    # 粒子（打击判定残片）
    Element("particle50", "粒子 (Particle)", "50 判定粒子",
            "osu!（标准）", False, "7x7", "Normal", "Centre"),
    Element("particle100", "粒子 (Particle)", "100 判定粒子",
            "osu!（标准）", False, "7x7", "Normal", "Centre"),
    Element("particle300", "粒子 (Particle)", "300 判定粒子",
            "osu!（标准）", False, "7x7", "Normal", "Centre"),
    # 灯光
    Element("lighting", "灯光 (Lighting)", "kiai 判定灯光（osu!/catch 共用）",
            "osu!（标准）", False, "100x100", "Additive", "Centre"),

    # ==================== osu!mania ====================
    # 音符
    Element("mania-note1", "音符 (Note)", "第 1 类单点音符", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-note2", "音符 (Note)", "第 2 类单点音符", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-noteS", "音符 (Note)", "特殊单点音符", "osu!mania", True, "", "Normal", "Bottom"),
    # 长条头
    Element("mania-note1H", "长条头 (Hold Head)", "第 1 类长条头部", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-note2H", "长条头 (Hold Head)", "第 2 类长条头部", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-noteSH", "长条头 (Hold Head)", "特殊长条头部", "osu!mania", True, "", "Normal", "Bottom"),
    # 长条身
    Element("mania-note1L", "长条身 (Hold Body)", "第 1 类长条身体", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-note2L", "长条身 (Hold Body)", "第 2 类长条身体", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-noteSL", "长条身 (Hold Body)", "特殊长条身体", "osu!mania", True, "", "Normal", "Bottom"),
    # 长条尾
    Element("mania-note1T", "长条尾 (Hold Tail)", "第 1 类长条尾部", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-note2T", "长条尾 (Hold Tail)", "第 2 类长条尾部", "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-noteST", "长条尾 (Hold Tail)", "特殊长条尾部", "osu!mania", True, "", "Normal", "Bottom"),
    # 按键
    Element("mania-key1", "按键 (Key)", "第 1 类按键·未按", "osu!mania", False, "50x107", "Normal", "Bottom"),
    Element("mania-key1D", "按键 (Key)", "第 1 类按键·按下", "osu!mania", False, "50x107", "Normal", "Bottom"),
    Element("mania-key2", "按键 (Key)", "第 2 类按键·未按", "osu!mania", False, "50x107", "Normal", "Bottom"),
    Element("mania-key2D", "按键 (Key)", "第 2 类按键·按下", "osu!mania", False, "50x107", "Normal", "Bottom"),
    Element("mania-keyS", "按键 (Key)", "特殊按键·未按", "osu!mania", False, "50x107", "Normal", "Bottom"),
    Element("mania-keySD", "按键 (Key)", "特殊按键·按下", "osu!mania", False, "50x107", "Normal", "Bottom"),
    # 判定
    Element("mania-hit0", "判定 (Judgement)", "Miss 判定", "osu!mania", True, "", "Normal", "Centre"),
    Element("mania-hit50", "判定 (Judgement)", "50 判定", "osu!mania", True, "", "Normal", "Centre"),
    Element("mania-hit100", "判定 (Judgement)", "100 判定", "osu!mania", True, "", "Normal", "Centre"),
    Element("mania-hit200", "判定 (Judgement)", "200 判定", "osu!mania", True, "", "Normal", "Centre"),
    Element("mania-hit300", "判定 (Judgement)", "300 判定", "osu!mania", True, "", "Normal", "Centre"),
    Element("mania-hit300g", "判定 (Judgement)", "300g（Geki 激）判定", "osu!mania", True, "", "Normal", "Centre"),
    # 舞台
    Element("mania-stage-left", "舞台 (Stage)", "左侧舞台边框（拉伸适应舞台高度）",
            "osu!mania", False, "高≤768px", "Normal", "BottomRight"),
    Element("mania-stage-right", "舞台 (Stage)", "右侧舞台边框（拉伸适应舞台高度）",
            "osu!mania", False, "高≤768px", "Normal", "BottomRight"),
    Element("mania-stage-bottom", "舞台 (Stage)", "底部舞台前景（覆盖全舞台；lazer 不拉伸到舞台宽）",
            "osu!mania", True, "", "Normal", "Bottom"),
    Element("mania-stage-light", "舞台 (Stage)", "舞台闪光（按键时显示，位于音符下方）",
            "osu!mania", True, "高≤768px", "Multiplicative", "Bottom"),
    Element("mania-stage-hint", "舞台 (Stage)", "图形判定线（绘制在整个舞台宽度上）",
            "osu!mania", False, "", "Normal", "Centre"),
    # 灯光
    Element("lightingL", "灯光 (Lighting)", "长按音符闪光（可动画；舞台颠倒时水平翻转）",
            "osu!mania", True, "", "Additive", "Centre"),
    Element("lightingN", "灯光 (Lighting)", "单音符闪光（用于单音符和长按尾）",
            "osu!mania", True, "", "Additive", "Centre"),
    # 连击
    Element("comboburst-mania", "连击 (Comboburst)", "连击爆发图（mania，显示于舞台右侧）",
            "osu!mania", False, "高≤768px", "Normal", "BottomLeft"),
    # 其它
    Element("mania-warningarrow", "其它 (Other)", "开局前警告箭头（应指向下方）",
            "osu!mania", False, "", "Normal", "Centre"),

    # ==================== osu!taiko（太鼓） ====================
    # 太鼓区域
    Element("taiko-bar-left", "太鼓区域 (Arena)", "太鼓左侧区域", "osu!taiko（太鼓）"),
    Element("taiko-bar-right", "太鼓区域 (Arena)", "太鼓右侧滚条（拉伸适应屏幕宽度）", "osu!taiko（太鼓）"),
    Element("taiko-bar-left-glow", "太鼓区域 (Arena)", "左鼓面发光", "osu!taiko（太鼓）"),
    Element("taiko-bar-right-glow", "太鼓区域 (Arena)", "滚条 Kiai 状态（覆盖 taiko-bar-right）", "osu!taiko（太鼓）"),
    Element("taiko-barline", "太鼓区域 (Arena)", "小节线（每个小节开始时显示）",
            "osu!taiko（太鼓）", False, "4x175", "Normal", "Centre"),
    Element("taiko-drum-inner", "太鼓区域 (Arena)", "太鼓内圈",
            "osu!taiko（太鼓）", False, "90x200", "Normal", "TopLeft"),
    Element("taiko-drum-outer", "太鼓区域 (Arena)", "太鼓外圈",
            "osu!taiko（太鼓）", False, "90x200", "Normal", "TopLeft"),
    Element("taiko-glow", "太鼓区域 (Arena)", "Kiai 打击位置发光（黄色着色，击打时扩大）",
            "osu!taiko（太鼓）", False, "", "Multiplicative", "Centre"),
    # 音符
    Element("taikohitcircle", "音符 (Note)", "普通音符（Don 红 Katsu 蓝）",
            "osu!taiko（太鼓）", False, "118x118", "Multiplicative", "Centre"),
    Element("taikohitcircleoverlay", "音符 (Note)", "普通音符外框（仅 2 帧，50 连击开始动画）",
            "osu!taiko（太鼓）", False, "118x118", "Normal", "Centre"),
    Element("taikobigcircle", "音符 (Note)", "大音符/终结音符（Don 红 Katsu 蓝，滚打起点黄色）",
            "osu!taiko（太鼓）", False, "118x118", "Multiplicative", "Centre"),
    Element("taikobigcircleoverlay", "音符 (Note)", "大音符外框（仅 2 帧动画）",
            "osu!taiko（太鼓）", False, "118x118", "Normal", "Centre"),
    # 滚打
    Element("taiko-roll-end", "滚打 (Roll)", "滚打末端（颜色从黄渐变到红）",
            "osu!taiko（太鼓）", False, "64x128", "Multiplicative", "TopLeft"),
    Element("taiko-roll-middle", "滚打 (Roll)", "滚打轨道（SD 图像宽度必须恰好 1px）",
            "osu!taiko（太鼓）", False, "1x128", "Multiplicative", "TopLeft"),
    # 摇器
    Element("taiko-spinner-warning", "摇器 (Spinner)", "摇器（转盘）警告标识",
            "osu!taiko（太鼓）", False, "", "Normal", "Centre"),
    # 太鼓小人
    Element("pippidonidle", "太鼓小人 (Pippidon)", "小人待机状态",
            "osu!taiko（太鼓）", False, "", "Normal", "BottomLeft"),
    Element("pippidonfail", "太鼓小人 (Pippidon)", "小人失败状态",
            "osu!taiko（太鼓）", False, "", "Normal", "BottomLeft"),
    Element("pippidonkiai", "太鼓小人 (Pippidon)", "小人 Kiai 状态",
            "osu!taiko（太鼓）", False, "", "Normal", "BottomLeft"),
    Element("pippidonclear", "太鼓小人 (Pippidon)", "小人连击里程碑状态",
            "osu!taiko（太鼓）", False, "", "Normal", "BottomLeft"),
    # 打击结果
    Element("taiko-hit0", "打击结果 (Hit)", "太鼓 Miss 打击结果", "osu!taiko（太鼓）", True),
    Element("taiko-hit100", "打击结果 (Hit)", "太鼓 100 打击结果", "osu!taiko（太鼓）", True),
    Element("taiko-hit100k", "打击结果 (Hit)", "太鼓 100k 打击结果", "osu!taiko（太鼓）", True),
    Element("taiko-hit300", "打击结果 (Hit)", "太鼓 300 打击结果", "osu!taiko（太鼓）", True),
    Element("taiko-hit300k", "打击结果 (Hit)", "太鼓 300k 打击结果", "osu!taiko（太鼓）", True),
    Element("taiko-hit300g", "打击结果 (Hit)", "太鼓 300g（仅结算屏幕使用，代替 taiko-hit300k）",
            "osu!taiko（太鼓）", False, "", "Normal", "Centre"),
    # 游玩区域
    Element("taiko-slider", "游玩区域 (Field)", "滚动条背景（从右向左无缝循环，游戏中放大 1.4 倍）",
            "osu!taiko（太鼓）", False, "776x162", "Normal", "TopLeft"),
    Element("taiko-slider-fail", "游玩区域 (Field)", "滚动条失败背景（Miss 或休息血量不足时）",
            "osu!taiko（太鼓）", False, "776x162", "Normal", "TopLeft"),
    Element("taiko-flower-group", "游玩区域 (Field)", "连击爆发花朵（从小人后方展开渐隐）",
            "osu!taiko（太鼓）", False, "", "Normal", "Bottom"),

    # ==================== osu!catch（接水果） ====================
    # 水果
    Element("fruit-catcher-idle", "水果 (Fruit)", "接水果角色·待机",
            "osu!catch（接水果）", True, "最小宽 302px", "Normal", "Top"),
    Element("fruit-catcher-fail", "水果 (Fruit)", "接水果角色·漏接",
            "osu!catch（接水果）", True, "", "Normal", "Centre"),
    Element("fruit-catcher-kiai", "水果 (Fruit)", "接水果角色·kiai",
            "osu!catch（接水果）", True, "", "Normal", "Centre"),
    Element("fruit-ryuuta", "水果 (Fruit)", "接水果角色（旧版 2.2-）",
            "osu!catch（接水果）", True, "", "Normal", "Centre"),
    Element("fruit-bananas", "水果 (Fruit)", "香蕉（转盘水果，黄色着色）",
            "osu!catch（接水果）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-bananas-overlay", "水果 (Fruit)", "香蕉外框（转盘）",
            "osu!catch（接水果）", False, "128x128", "Normal", "Centre"),
    Element("fruit-apple", "水果 (Fruit)", "苹果（第三个水果）",
            "osu!catch（接水果）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-apple-overlay", "水果 (Fruit)", "苹果外框",
            "osu!catch（接水果）", False, "128x128", "Normal", "Centre"),
    Element("fruit-grapes", "水果 (Fruit)", "葡萄（第二个水果）",
            "osu!catch（接水果）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-grapes-overlay", "水果 (Fruit)", "葡萄外框",
            "osu!catch（接水果）", False, "128x128", "Normal", "Centre"),
    Element("fruit-orange", "水果 (Fruit)", "橘子（最后一个水果）",
            "osu!catch（接水果）", True, "128x128", "Multiplicative", "Centre"),
    Element("fruit-orange-overlay", "水果 (Fruit)", "橘子外框",
            "osu!catch（接水果）", True, "128x128", "Normal", "Centre"),
    Element("fruit-pear", "水果 (Fruit)", "梨（第一个水果，用于 HyperDash）",
            "osu!catch（接水果）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-pear-overlay", "水果 (Fruit)", "梨外框",
            "osu!catch（接水果）", False, "128x128", "Normal", "Centre"),
    Element("fruit-drop", "水果 (Fruit)", "水滴（滑条水果，用连击色着色）",
            "osu!catch（接水果）", True, "128x128", "Multiplicative", "Centre"),
    Element("fruit-drop-overlay", "水果 (Fruit)", "水滴外框（滑条）",
            "osu!catch（接水果）", False, "128x128", "Normal", "Centre"),
    # 连击
    Element("comboburst-fruits", "连击 (Comboburst)", "连击爆发图（osu!catch 专用，应面向右方）",
            "osu!catch（接水果）", False),
]

_ELEM_BY_NAME = {e.filename: e for e in ELEMENTS}


def by_name(name: str) -> Element | None:
    return _ELEM_BY_NAME.get(name)


def by_group() -> dict:
    """返回 {模式分组: {功能分类: [元素]}}，保持 GROUPS 定义顺序。"""
    result: dict = {g: {c: [] for c in cats} for g, cats in GROUPS.items()}
    for e in ELEMENTS:
        if e.group in result and e.category in result[e.group]:
            result[e.group][e.category].append(e)
    return result


def by_category() -> dict:
    """兼容旧接口：返回 {分类名: [元素]}，按平铺后的分类顺序。"""
    result: dict = {c: [] for c in CATEGORIES}
    for e in ELEMENTS:
        if e.category in result:
            result[e.category].append(e)
    return result