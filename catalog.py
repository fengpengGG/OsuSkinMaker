"""osu! 皮肤元素目录（mania 为重点，另含各模式通用元素）。

数据来源：osu! 官方 wiki（Skinning）。
用于元素管理界面：按分类展示、检测缺失、预览。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Element:
    filename: str       # 基础文件名（不含扩展名）
    category: str       # 分类
    description: str    # 中文说明
    animatable: bool = False   # 是否支持 -{n} 帧动画
    size: str = ""              # 建议尺寸
    blend: str = "Normal"       # 混合模式
    origin: str = "Bottom"      # 原点


# 分类名（保持顺序）
CATEGORIES = [
    "判定 (Judgement)",
    "连击 (Comboburst)",
    "按键 (Key)",
    "音符 (Note)",
    "长条头 (Hold Head)",
    "长条身 (Hold Body)",
    "长条尾 (Hold Tail)",
    "舞台 (Stage)",
    "灯光 (Lighting)",
    "其它 (Other)",
    "光标 (Cursor)",
    "打击圈 (Hitcircle)",
    "打击判定 (Hitburst)",
    "滑条 (Slider)",
    "转盘 (Spinner)",
    "结算 (Ranking)",
    "游玩界面 (Play)",
    "主菜单 (Menu)",
    "暂停界面 (Pause)",
    "失败界面 (Fail)",
    "太鼓 (Taiko)",
    "接水果 (Catch)",
    "分数与准确度 (Score & Acc)",
    "血条 (Scorebar)",
]

ELEMENTS: list = [
    # 判定
    Element("mania-hit0", "判定 (Judgement)", "Miss 判定", True, "", "Normal", "Centre"),
    Element("mania-hit50", "判定 (Judgement)", "50 判定", True, "", "Normal", "Centre"),
    Element("mania-hit100", "判定 (Judgement)", "100 判定", True, "", "Normal", "Centre"),
    Element("mania-hit200", "判定 (Judgement)", "200 判定", True, "", "Normal", "Centre"),
    Element("mania-hit300", "判定 (Judgement)", "300 判定", True, "", "Normal", "Centre"),
    Element("mania-hit300g", "判定 (Judgement)", "300g（Geki 激）判定", True, "", "Normal", "Centre"),
    # 连击
    Element("comboburst", "连击 (Comboburst)", "连击爆发图（osu! 标准模式，v2.3+ 各模式用专用版本）", True, "", "Normal", "Centre"),
    Element("comboburst-mania", "连击 (Comboburst)", "连击爆发图（mania，显示于舞台右侧）", False, "高≤768px", "Normal", "BottomLeft"),
    # 按键
    Element("mania-key1", "按键 (Key)", "第 1 类按键·未按", False, "50x107", "Normal", "Bottom"),
    Element("mania-key1D", "按键 (Key)", "第 1 类按键·按下", False, "50x107", "Normal", "Bottom"),
    Element("mania-key2", "按键 (Key)", "第 2 类按键·未按", False, "50x107", "Normal", "Bottom"),
    Element("mania-key2D", "按键 (Key)", "第 2 类按键·按下", False, "50x107", "Normal", "Bottom"),
    Element("mania-keyS", "按键 (Key)", "特殊按键·未按", False, "50x107", "Normal", "Bottom"),
    Element("mania-keySD", "按键 (Key)", "特殊按键·按下", False, "50x107", "Normal", "Bottom"),
    # 音符
    Element("mania-note1", "音符 (Note)", "第 1 类单点音符", True, "", "Normal", "Bottom"),
    Element("mania-note2", "音符 (Note)", "第 2 类单点音符", True, "", "Normal", "Bottom"),
    Element("mania-noteS", "音符 (Note)", "特殊单点音符", True, "", "Normal", "Bottom"),
    # 长条头
    Element("mania-note1H", "长条头 (Hold Head)", "第 1 类长条头部", True, "", "Normal", "Bottom"),
    Element("mania-note2H", "长条头 (Hold Head)", "第 2 类长条头部", True, "", "Normal", "Bottom"),
    Element("mania-noteSH", "长条头 (Hold Head)", "特殊长条头部", True, "", "Normal", "Bottom"),
    # 长条身
    Element("mania-note1L", "长条身 (Hold Body)", "第 1 类长条身体", True, "", "Normal", "Bottom"),
    Element("mania-note2L", "长条身 (Hold Body)", "第 2 类长条身体", True, "", "Normal", "Bottom"),
    Element("mania-noteSL", "长条身 (Hold Body)", "特殊长条身体", True, "", "Normal", "Bottom"),
    # 长条尾
    Element("mania-note1T", "长条尾 (Hold Tail)", "第 1 类长条尾部", True, "", "Normal", "Bottom"),
    Element("mania-note2T", "长条尾 (Hold Tail)", "第 2 类长条尾部", True, "", "Normal", "Bottom"),
    Element("mania-noteST", "长条尾 (Hold Tail)", "特殊长条尾部", True, "", "Normal", "Bottom"),
    # 舞台
    Element("mania-stage-left", "舞台 (Stage)", "左侧舞台边框（拉伸适应舞台高度）", False, "高≤768px", "Normal", "BottomRight"),
    Element("mania-stage-right", "舞台 (Stage)", "右侧舞台边框（拉伸适应舞台高度）", False, "高≤768px", "Normal", "BottomRight"),
    Element("mania-stage-bottom", "舞台 (Stage)", "底部舞台前景（覆盖全舞台；lazer 不拉伸到舞台宽）", True, "", "Normal", "Bottom"),
    Element("mania-stage-light", "舞台 (Stage)", "舞台闪光（按键时显示，位于音符下方）", True, "高≤768px", "Multiplicative", "Bottom"),
    Element("mania-stage-hint", "舞台 (Stage)", "图形判定线（绘制在整个舞台宽度上）", False, "", "Normal", "Centre"),
    # 灯光
    Element("lightingL", "灯光 (Lighting)", "长按音符闪光（可动画；舞台颠倒时水平翻转）", True, "", "Additive", "Centre"),
    Element("lightingN", "灯光 (Lighting)", "单音符闪光（用于单音符和长按尾）", True, "", "Additive", "Centre"),
    # 其它
    Element("mania-warningarrow", "其它 (Other)", "开局前警告箭头（应指向下方）", False, "", "Normal", "Centre"),

    # ---- 通用元素（非 mania）----
    # 光标
    Element("cursor", "光标 (Cursor)", "光标主体", False, "", "Normal", "Centre"),
    Element("cursortrail", "光标 (Cursor)", "光标拖尾", False, "", "Normal", "Centre"),
    Element("cursormiddle", "光标 (Cursor)", "光标中心点（可选）", False, "", "Normal", "Centre"),
    Element("cursor-smoke", "光标 (Cursor)", "拉烟效果（按住拉烟键时显示）", False, "", "Normal", "Centre"),
    # 打击圈
    Element("hitcircle", "打击圈 (Hitcircle)", "打击圈主体（点击前渐隐，点击时展开）", False, "128x128", "Multiplicative", "Centre"),
    Element("hitcircleoverlay", "打击圈 (Hitcircle)", "打击圈外框（可在数字上方或下方）", False, "128x128", "Normal", "Centre"),
    Element("hitcircleselect", "打击圈 (Hitcircle)", "编辑器中选中的打击圈", False, "128x128", "Normal", "Centre"),
    Element("approachcircle", "打击圈 (Hitcircle)", "缩圈（用连击色着色，随时间缩小）", False, "126x126", "Multiplicative", "Centre"),
    Element("followpoint", "打击圈 (Hitcircle)", "连接线箭头（应指向右方）", True, "", "Normal", "Centre"),
    # 打击判定
    Element("hit300", "打击判定 (Hitburst)", "300 判定", True),
    Element("hit300g", "打击判定 (Hitburst)", "300g (Geki) 判定", True),
    Element("hit300k", "打击判定 (Hitburst)", "300k (Katu) 判定（结算屏幕不显示）", True),
    Element("hit100", "打击判定 (Hitburst)", "100 判定", True),
    Element("hit100k", "打击判定 (Hitburst)", "100k (Katu) 判定", True),
    Element("hit50", "打击判定 (Hitburst)", "50 判定", True),
    Element("hit0", "打击判定 (Hitburst)", "Miss 判定", True),
    # 滑条
    Element("sliderb", "滑条 (Slider)", "滑条球动画（sliderb0, sliderb1…）", True),
    Element("sliderb-nd", "滑条 (Slider)", "滑条球黑底（默认球）", False),
    Element("sliderb-spec", "滑条 (Slider)", "滑条球高光层（默认球）", False),
    Element("sliderstartcircle", "滑条 (Slider)", "滑条起点圈（覆盖 hitcircle）", False, "128x128", "Multiplicative", "Centre"),
    Element("sliderstartcircleoverlay", "滑条 (Slider)", "滑条起点圈外框（需配合起点圈）", False, "128x128", "Normal", "Centre"),
    Element("sliderendcircle", "滑条 (Slider)", "滑条终点圈（覆盖 hitcircle）", False, "128x128", "Multiplicative", "Centre"),
    Element("sliderendcircleoverlay", "滑条 (Slider)", "滑条终点圈外框（需配合终点圈）", False, "128x128", "Normal", "Centre"),
    Element("sliderscorepoint", "滑条 (Slider)", "滑条点（也用于太鼓滚打点）", False, "16x16", "Normal", "Centre"),
    Element("sliderfollowcircle", "滑条 (Slider)", "滑条跟随圈（收集滑条点时短暂扩大）", True),
    Element("reversearrow", "滑条 (Slider)", "折返箭头", False, "128x128", "Normal", "Centre"),
    # 转盘（旧版 <2.0）
    Element("spinner-circle", "转盘 (Spinner)", "转盘圆圈（旧版 <2.0）", False),
    Element("spinner-background", "转盘 (Spinner)", "转盘背景（旧版 <2.0）", False, "1024x702", "Multiplicative", "Centre"),
    Element("spinner-metre", "转盘 (Spinner)", "转盘进度条（旧版 <2.0）", False),
    # 转盘（新版 >=2.0）
    Element("spinner-top", "转盘 (Spinner)", "转盘顶层（旋转第二快，中间层）", False),
    Element("spinner-bottom", "转盘 (Spinner)", "转盘底层（旋转最慢）", False),
    Element("spinner-middle", "转盘 (Spinner)", "转盘中间层（随时间变红作时间指示）", False),
    Element("spinner-middle2", "转盘 (Spinner)", "转盘中层（旋转最快，第二高层）", False),
    Element("spinner-glow", "转盘 (Spinner)", "转盘光晕（青色着色，奖励分时闪白）", False, "", "Additive", "Centre"),
    Element("spinner-approachcircle", "转盘 (Spinner)", "转盘缩圈（新版 >=2.0）", False, "384x384", "Normal", "Centre"),
    Element("spinner-rpm", "转盘 (Spinner)", "转速显示器（RPM）", False, "280x56", "Normal", "TopLeft"),
    Element("spinner-spin", "转盘 (Spinner)", "转盘旋转提示（开始时显示）", False),
    Element("spinner-clear", "转盘 (Spinner)", "转盘完成标识（达成要求时显示）", False),
    # 粒子（打击判定残片）
    Element("particle50", "其它 (Other)", "50 判定粒子", False, "7x7", "Normal", "Centre"),
    Element("particle100", "其它 (Other)", "100 判定粒子", False, "7x7", "Normal", "Centre"),
    Element("particle300", "其它 (Other)", "300 判定粒子", False, "7x7", "Normal", "Centre"),
    # 结算
    Element("ranking-xh", "结算 (Ranking)", "SS+ 判定（隐/闪）", False),
    Element("ranking-x", "结算 (Ranking)", "SS 判定", False),
    Element("ranking-sh", "结算 (Ranking)", "S+ 判定（隐/闪）", False),
    Element("ranking-s", "结算 (Ranking)", "S 判定", False),
    Element("ranking-a", "结算 (Ranking)", "A 判定", False),
    Element("ranking-b", "结算 (Ranking)", "B 判定", False),
    Element("ranking-c", "结算 (Ranking)", "C 判定", False),
    Element("ranking-d", "结算 (Ranking)", "D 判定", False),
    Element("ranking-replay", "结算 (Ranking)", "重播按键", False),
    Element("ranking-retry", "结算 (Ranking)", "重试按键（旧版）", False),
    # 游玩界面
    Element("play-skip", "游玩界面 (Play)", "游玩“跳过”按钮（休息段，拉伸贴边；可动画）", False, "", "Multiplicative", "BottomRight"),
    # 主菜单
    Element("menu-background", "主菜单 (Menu)", "主菜单背景（.jpg）", False),
    Element("welcome_text", "主菜单 (Menu)", "欢迎文字", False),
    Element("menu-snow", "主菜单 (Menu)", "主菜单雪花", False),
    # 太鼓
    Element("taiko-bar-left", "太鼓 (Taiko)", "太鼓左侧区域", False),
    Element("taiko-bar-right", "太鼓 (Taiko)", "太鼓右侧滚条（拉伸适应屏幕宽度）", False),
    Element("taiko-bar-left-glow", "太鼓 (Taiko)", "左鼓面发光", False),
    Element("taiko-bar-right-glow", "太鼓 (Taiko)", "滚条 Kiai 状态（覆盖 taiko-bar-right）", False),
    Element("taiko-hit0", "太鼓 (Taiko)", "太鼓 Miss 打击结果", True),
    Element("taiko-hit100", "太鼓 (Taiko)", "太鼓 100 打击结果", True),
    Element("taiko-hit100k", "太鼓 (Taiko)", "太鼓 100k 打击结果", True),
    Element("taiko-hit300", "太鼓 (Taiko)", "太鼓 300 打击结果", True),
    Element("taiko-hit300k", "太鼓 (Taiko)", "太鼓 300k 打击结果", True),
    # 接水果
    Element("fruit-catcher-idle", "接水果 (Catch)", "接水果角色·待机", True, "最小宽 302px", "Normal", "Top"),
    Element("fruit-catcher-fail", "接水果 (Catch)", "接水果角色·漏接", True, "", "Normal", "Centre"),
    Element("fruit-catcher-kiai", "接水果 (Catch)", "接水果角色·kiai", True, "", "Normal", "Centre"),
    Element("fruit-ryuuta", "接水果 (Catch)", "接水果角色（旧版 2.2-）", True, "", "Normal", "Centre"),
    Element("fruit-bananas", "接水果 (Catch)", "香蕉（转盘水果，黄色着色）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-bananas-overlay", "接水果 (Catch)", "香蕉外框（转盘）", False, "128x128", "Normal", "Centre"),
    Element("fruit-apple", "接水果 (Catch)", "苹果（第三个水果）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-apple-overlay", "接水果 (Catch)", "苹果外框", False, "128x128", "Normal", "Centre"),
    Element("fruit-grapes", "接水果 (Catch)", "葡萄（第二个水果）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-grapes-overlay", "接水果 (Catch)", "葡萄外框", False, "128x128", "Normal", "Centre"),
    Element("fruit-orange", "接水果 (Catch)", "橘子（最后一个水果）", True, "128x128", "Multiplicative", "Centre"),
    Element("fruit-orange-overlay", "接水果 (Catch)", "橘子外框", True, "128x128", "Normal", "Centre"),
    Element("fruit-pear", "接水果 (Catch)", "梨（第一个水果，用于 HyperDash）", False, "128x128", "Multiplicative", "Centre"),
    Element("fruit-pear-overlay", "接水果 (Catch)", "梨外框", False, "128x128", "Normal", "Centre"),
    Element("fruit-drop", "接水果 (Catch)", "水滴（滑条水果，用连击色着色）", True, "128x128", "Multiplicative", "Centre"),
    Element("fruit-drop-overlay", "接水果 (Catch)", "水滴外框（滑条）", False, "128x128", "Normal", "Centre"),
    Element("comboburst-fruits", "接水果 (Catch)", "连击爆发图（osu!catch 专用，应面向右方）", False),
    # 分数与准确度（数字/标点，前缀默认 score，可在 [Fonts] 里改 ScorePrefix / ComboPrefix）
    Element("score-0", "分数与准确度 (Score & Acc)", "数字 0", False),
    Element("score-1", "分数与准确度 (Score & Acc)", "数字 1", False),
    Element("score-2", "分数与准确度 (Score & Acc)", "数字 2", False),
    Element("score-3", "分数与准确度 (Score & Acc)", "数字 3", False),
    Element("score-4", "分数与准确度 (Score & Acc)", "数字 4", False),
    Element("score-5", "分数与准确度 (Score & Acc)", "数字 5", False),
    Element("score-6", "分数与准确度 (Score & Acc)", "数字 6", False),
    Element("score-7", "分数与准确度 (Score & Acc)", "数字 7", False),
    Element("score-8", "分数与准确度 (Score & Acc)", "数字 8", False),
    Element("score-9", "分数与准确度 (Score & Acc)", "数字 9", False),
    Element("score-comma", "分数与准确度 (Score & Acc)", "千位分隔符 ,", False),
    Element("score-dot", "分数与准确度 (Score & Acc)", "小数点 .", False),
    Element("score-percent", "分数与准确度 (Score & Acc)", "百分号 %", False),
    Element("score-x", "分数与准确度 (Score & Acc)", "连击乘号 ×", False),
    # 连击数字（前缀默认 combo，可在 [Fonts] 里改 ComboPrefix）
    Element("combo-0", "分数与准确度 (Score & Acc)", "连击数字 0", False),
    Element("combo-1", "分数与准确度 (Score & Acc)", "连击数字 1", False),
    Element("combo-2", "分数与准确度 (Score & Acc)", "连击数字 2", False),
    Element("combo-3", "分数与准确度 (Score & Acc)", "连击数字 3", False),
    Element("combo-4", "分数与准确度 (Score & Acc)", "连击数字 4", False),
    Element("combo-5", "分数与准确度 (Score & Acc)", "连击数字 5", False),
    Element("combo-6", "分数与准确度 (Score & Acc)", "连击数字 6", False),
    Element("combo-7", "分数与准确度 (Score & Acc)", "连击数字 7", False),
    Element("combo-8", "分数与准确度 (Score & Acc)", "连击数字 8", False),
    Element("combo-9", "分数与准确度 (Score & Acc)", "连击数字 9", False),
    Element("combo-comma", "分数与准确度 (Score & Acc)", "连击千位分隔符 ,", False),
    Element("combo-dot", "分数与准确度 (Score & Acc)", "连击小数点 .", False),
    Element("combo-percent", "分数与准确度 (Score & Acc)", "连击百分号 %", False),
    Element("combo-x", "分数与准确度 (Score & Acc)", "连击乘号 x", False),
    # 血条（mania 中垂直显示在场地右侧）
    Element("scorebar-bg", "血条 (Scorebar)", "分数条（HP 血量）背景", False),
    Element("scorebar-colour", "血条 (Scorebar)", "分数条颜色层（靠近危险区变黑变红）", False),
    Element("scorebar-marker", "血条 (Scorebar)", "分数条标记（覆盖 ki 系列）", False),
    Element("scorebar-ki", "血条 (Scorebar)", "分数条通过标记（旧版，可被 marker 覆盖）", False),
    Element("scorebar-kidanger", "血条 (Scorebar)", "分数条警告标记（旧版）", False),
    Element("scorebar-kidanger2", "血条 (Scorebar)", "分数条危急标记（旧版）", False),
    # 暂停界面（覆盖在游玩画面之上；按钮 Center 锚在画面中心纵线上）
    Element("pause-overlay", "暂停界面 (Pause)", "暂停覆盖层（Center，覆盖整个画面）", False, "1366x768", "Normal", "Centre"),
    Element("pause-continue", "暂停界面 (Pause)", "继续按钮（回到游戏，中心 y≈100）", False, "", "Normal", "Centre"),
    Element("pause-retry", "暂停界面 (Pause)", "重试按钮（中心 y≈178）", False, "", "Normal", "Centre"),
    Element("pause-back", "暂停界面 (Pause)", "返回按钮（退出到主菜单，中心 y≈256）", False, "", "Normal", "Centre"),
    # 失败界面
    Element("fail-background", "失败界面 (Fail)", "失败界面背景（Center，覆盖整个画面）", False, "1366x768", "Normal", "Centre"),
    # 其它
    Element("lighting", "其它 (Other)", "kiai 判定灯光（osu!/catch 共用）", False, "100x100", "Additive", "Centre"),
]

_ELEM_BY_NAME = {e.filename: e for e in ELEMENTS}


def by_name(name: str) -> Element | None:
    return _ELEM_BY_NAME.get(name)


def by_category() -> dict:
    result: dict = {}
    for cat in CATEGORIES:
        result[cat] = [e for e in ELEMENTS if e.category == cat]
    return result
