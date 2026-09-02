"""skin.ini 解析、序列化与命令 schema 定义。

skin.ini 是 osu! 皮肤的核心配置文件，格式与 INI 类似但有几个特点：
- 命令名区分大小写（例如 [Colours] 不能写成 [Colors]）
- 允许多个同名区块（尤其是 [Mania]，每个键数一个区块）
- 注释使用 ``//``
- 每列命令用 ``{n0}``（0 起）与 ``{n1}``（1 起）作为列号占位符，
  渲染时由 ``str.format`` 替换为 ``Colour1``、``NoteImage0H`` 等真实命令名
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class Entry:
    """区块内的一条记录：命令 或 注释/空行。"""
    key: str = ""          # 命令名；注释/空行为空
    value: str = ""        # 命令值；注释保存为原始文本
    is_comment: bool = False


@dataclass
class Section:
    """一个 [区块]。"""
    name: str
    entries: list = field(default_factory=list)

    def get(self, key: str) -> Optional[str]:
        for e in self.entries:
            if not e.is_comment and e.key == key:
                return e.value
        return None

    def set(self, key: str, value: str) -> None:
        """更新已有命令，否则追加到区块末尾。"""
        for e in self.entries:
            if not e.is_comment and e.key == key:
                e.value = value
                return
        self.entries.append(Entry(key=key, value=value))

    def keys(self) -> list:
        return [e.key for e in self.entries if not e.is_comment]


@dataclass
class SkinIni:
    """整个 skin.ini 文件。"""
    sections: list = field(default_factory=list)

    # -- 解析 --------------------------------------------------------------
    @classmethod
    def parse(cls, text: str) -> "SkinIni":
        ini = cls()
        current: Optional[Section] = None
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                if current is not None:
                    current.entries.append(Entry(is_comment=True, value=""))
                continue
            if line.startswith("["):
                name = line[1:-1].strip() if line.endswith("]") else line[1:].strip()
                current = Section(name=name)
                ini.sections.append(current)
            elif line.startswith("//") or line.startswith("#"):
                # osu! 注释以 // 开头；# 也兼容，但会与 mania 列命令名冲突，
                # 所以仅在行首出现 # 时视为注释。
                if current is not None:
                    current.entries.append(Entry(is_comment=True, value=raw))
            elif ":" in line:
                key, _, value = line.partition(":")
                if current is not None:
                    # osu! 官方规则：// 到行尾皆为注释，须从值中剥离，
                    # 否则如 "Keys: 4   //注释" 会读成带尾巴的字符串导致匹配失败
                    value = value.split("//", 1)[0].strip()
                    current.entries.append(Entry(key=key.strip(), value=value))
            else:
                # 无法识别的行，保留原文作为注释，避免破坏文件。
                if current is not None:
                    current.entries.append(Entry(is_comment=True, value=raw))
        return ini

    # -- 序列化 --------------------------------------------------------------
    def serialize(self) -> str:
        lines: list = []
        for sec in self.sections:
            lines.append(f"[{sec.name}]")
            for e in sec.entries:
                if e.is_comment:
                    lines.append(e.value if e.value else "")
                else:
                    lines.append(f"{e.key}: {e.value}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    # -- 便捷访问 --------------------------------------------------------------
    def section(self, name: str) -> Optional[Section]:
        for sec in self.sections:
            if sec.name == name:
                return sec
        return None

    def sections_named(self, name: str) -> list:
        return [sec for sec in self.sections if sec.name == name]

    def get(self, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        sec = self.section(section)
        if sec is None:
            return default
        v = sec.get(key)
        return default if v is None else v

    def set(self, section: str, key: str, value: str) -> None:
        sec = self.section(section)
        if sec is None:
            sec = Section(name=section)
            self.sections.append(sec)
        sec.set(key, str(value))


# ---------------------------------------------------------------------------
# 命令 schema（用于 GUI 渲染合适的输入控件）
# ---------------------------------------------------------------------------
# type 取值：
#   text   任意文本
#   int    整数
#   number 数字（可含小数）
#   bool   0/1
#   rgb    "R,G,B"
#   rgba   "R,G,B,A"
#   list   逗号分隔数字
#   choice 0/1/2（配 choices 标签）
#   keys   键数（1~18）

@dataclass
class Command:
    key: str
    type: str
    label: str
    default: str = ""
    choices: tuple = ()
    help: str = ""


GENERAL_COMMANDS = [
    Command("Name", "text", "皮肤名称", ""),
    Command("Author", "text", "作者", ""),
    Command("Version", "text", "皮肤版本", "latest", help="1.0/2.x/latest；缺省为 1.0"),
    Command("AnimationFramerate", "int", "动画帧率", "-1", help="-1 表示一秒播放完所有帧"),
    Command("SliderBallFlip", "bool", "滑条球翻转", "1"),
    Command("AllowSliderBallTint", "bool", "滑条球着色", "0"),
    Command("CursorRotate", "bool", "光标旋转", "1"),
    Command("CursorExpand", "bool", "光标点击放大", "1"),
    Command("CursorCentre", "bool", "光标居中原点", "1"),
    Command("CursorTrailRotate", "bool", "光标拖尾旋转", "1"),
    Command("HitCircleOverlayAboveNumber", "bool", "圈覆盖层在数字上方", "1"),
    Command("LayeredHitSounds", "bool", "叠加打击音", "1"),
    Command("SpinnerFadePlayfield", "bool", "转盘黑边", "0"),
    Command("SpinnerFrequencyModulate", "bool", "转盘音调变化", "1"),
    Command("SpinnerNoBlink", "bool", "转盘进度条不闪烁", "0"),
    Command("ComboBurstRandom", "bool", "连击图随机顺序", "0"),
    Command("CustomComboBurstSounds", "text", "自定义连击爆发音效连击数", "", help="逗号分隔的连击数列表"),
]

COLOUR_COMMANDS = [
    Command("Combo1", "rgb", "连击色 1", "255,192,0"),
    Command("Combo2", "rgb", "连击色 2", "0,202,0"),
    Command("Combo3", "rgb", "连击色 3", "18,124,255"),
    Command("Combo4", "rgb", "连击色 4", "242,24,57"),
    Command("Combo5", "rgb", "连击色 5", ""),
    Command("Combo6", "rgb", "连击色 6", ""),
    Command("Combo7", "rgb", "连击色 7", ""),
    Command("Combo8", "rgb", "连击色 8", ""),
    Command("SliderBorder", "rgb", "滑条边框", "255,255,255"),
    Command("SliderTrackOverride", "rgb", "滑条轨道统一色", "", help="留空则使用连击色"),
    Command("SliderBall", "rgb", "滑条球颜色", "2,170,255"),
    Command("MenuGlow", "rgb", "主菜单光谱条颜色", "0,78,155"),
    Command("SongSelectActiveText", "rgb", "选中曲目文字色", "0,0,0"),
    Command("SongSelectInactiveText", "rgb", "未选曲目文字色", "255,255,255"),
    Command("InputOverlayText", "rgb", "输入覆盖层文字色", "255,255,255"),
    Command("SpinnerBackground", "rgb", "转盘背景色", "100,100,100"),
    Command("StarBreakAdditive", "rgb", "休息段 star2 附加色", "255,182,193"),
]

FONT_COMMANDS = [
    Command("HitCirclePrefix", "fontprefix", "打击圈数字前缀", "default"),
    Command("HitCircleOverlap", "int", "打击圈数字重叠", "-2", help="负数产生间隔"),
    Command("ScorePrefix", "fontprefix", "分数数字前缀", "score"),
    Command("ScoreOverlap", "int", "分数数字重叠", "0"),
    Command("ComboPrefix", "fontprefix", "连击数字前缀", "score"),
    Command("ComboOverlap", "int", "连击数字重叠", "0"),
]

# Mania 区块命令（# 为列占位符，渲染时按 Keys 展开）
MANIA_COMMANDS = [
    Command("Keys", "keys", "键数", "4"),
    Command("ColumnStart", "number", "左列起点", "136", help="第一列左缘距舞台左缘的距离（480px 高坐标系）"),
    Command("ColumnRight", "number", "右边界", "19", help="最后一列右缘距舞台右缘的距离（480px 高坐标系）"),
    Command("ColumnWidth", "list", "每列宽度", "30", help="逗号分隔，可每列不同；效果随 NoteBodyStyle 而定"),
    Command("ColumnSpacing", "list", "列间距", "0"),
    Command("ColumnLineWidth", "list", "列分隔线宽", "2"),
    Command("HitPosition", "int", "判定线高度", "402", help="音符落到该高度时判定；480px 高坐标系"),
    Command("LightPosition", "int", "灯光高度", "413", help="stage-light 的显示位置，一般低于判定线"),
    Command("LightFramePerSecond", "int", "舞台灯光动画帧率", "", help="stage-light 贴图的动画帧率；缺省 60"),
    Command("ScorePosition", "int", "判定提示高度", "300", help="hitburst/判定评分在场地中的垂直位置（0=顶，480=底）"),
    Command("ComboPosition", "int", "连击计数高度", "111", help="连击数字在场地中的垂直位置（0=顶，480=底）"),
    Command("BarlineHeight", "number", "小节线厚度", "1.2"),
    Command("ColourBarline", "rgb", "小节线颜色", "255,255,255"),
    Command("JudgementLine", "bool", "显示判定线", "1"),
    Command("ColourJudgementLine", "rgb", "判定线颜色", "255,255,255", help="默认可见；该字段对判定线颜色生效"),
    Command("ColourColumnLine", "rgba", "列分隔线颜色", "255,255,255,255"),
    Command("ColourHold", "rgba", "长条身体着色", "255,255,255,255", help="覆盖长条身体颜色（RGBA）"),
    Command("ColourBreak", "rgba", "休息段音符着色", "255,255,255,255", help="覆盖休息段音符颜色（RGBA）"),
    Command("ColourKeyWarning", "rgb", "按键警告颜色", "255,255,255", help="按键未按时提示覆盖色（RGB）"),
    Command("SpecialStyle", "choice", "特殊样式", "0", choices=("0=无", "1=左/外", "2=右/内")),
    Command("ComboBurstStyle", "choice", "连击图位置", "1", choices=("0=左", "1=右", "2=两侧")),
    Command("SplitStages", "bool", "分离为两个舞台", "0", help="上下分割；1 时特效/连击图分别显示在下/上舞台"),
    Command("StageSeparation", "number", "舞台间距", "40", help="SplitStages=1 时两舞台之间的间隔"),
    Command("SeparateScore", "bool", "判定只显示在对应舞台", "1"),
    Command("KeysUnderNotes", "bool", "按键被音符覆盖", "0"),
    Command("UpsideDown", "bool", "始终倒置", "0"),
    Command("KeyFlipWhenUpsideDown", "bool", "倒置时翻转按键", "1"),
    Command("NoteFlipWhenUpsideDown", "bool", "倒置时翻转音符", "1"),
    Command("NoteBodyStyle", "choice", "长条身体样式", "1", choices=("0=拉伸", "1=从顶", "2=从底")),
    Command("WidthForNoteHeightScale", "number", "音符高度缩放基准宽", "", help="列宽不同时以最窄列为准"),
    # 舞台 / 通用贴图
    Command("StageLeft", "image", "左舞台贴图", "", help="mania-stage-left.png"),
    Command("StageRight", "image", "右舞台贴图", "", help="mania-stage-right.png"),
    Command("StageBottom", "image", "底部舞台贴图", "", help="mania-stage-bottom.png"),
    Command("StageHint", "image", "判定线贴图", "", help="mania-stage-hint.png"),
    Command("StageLight", "image", "舞台灯光贴图", "", help="mania-stage-light.png"),
    Command("LightingN", "image", "单点灯光贴图", "", help="lightingN.png"),
    Command("LightingL", "image", "长条灯光贴图", "", help="lightingL.png"),
    Command("LightingNWidth", "number", "单点灯光宽度", "", help="灯光贴图拉伸到的宽度"),
    Command("LightingLWidth", "number", "长条灯光宽度", "", help="灯光贴图拉伸到的宽度"),
    Command("WarningArrow", "image", "警告箭头贴图", "", help="mania-warningarrow.png"),
    Command("Hit0", "image", "Hit0 贴图", ""),
    Command("Hit50", "image", "Hit50 贴图", ""),
    Command("Hit100", "image", "Hit100 贴图", ""),
    Command("Hit200", "image", "Hit200 贴图", ""),
    Command("Hit300", "image", "Hit300 贴图", ""),
    Command("Hit300g", "image", "Hit300g 贴图", ""),
]

# 每列命令。
# 注意 osu! 的编号不一致：Colour / ColourLight 从 1 起（第 1 列 = Colour1），
# 而 NoteImage / KeyImage 从 0 起（第 1 列 = NoteImage0）。
# 这里用 {n0} 表示 0 起列号、{n1} 表示 1 起列号，渲染时由 str.format 替换。
MANIA_COLUMN_COMMANDS = [
    Command("Colour{n1}", "rgba", "第{n1}列轨道颜色", "0,0,0,255"),
    Command("ColourLight{n1}", "rgb", "第{n1}列灯光颜色", "55,255,255"),
    Command("KeyImage{n0}", "image", "第{n1}列未按按键图", ""),
    Command("KeyImage{n0}D", "image", "第{n1}列按下按键图", ""),
    Command("NoteImage{n0}", "image", "第{n1}列音符图", ""),
    Command("NoteImage{n0}H", "image", "第{n1}列长条头图", ""),
    Command("NoteImage{n0}L", "image", "第{n1}列长条身图", ""),
    Command("NoteImage{n0}T", "image", "第{n1}列长条尾图", ""),
]

# 每键数默认音符布局（列 -> note 序号，用于生成默认 NoteImage）
NOTE_LAYOUT = {
    1: ["S"],
    2: ["1", "1"],
    3: ["1", "S", "1"],
    4: ["1", "2", "2", "1"],
    5: ["1", "2", "S", "2", "1"],
    6: ["1", "2", "1", "1", "2", "1"],
    7: ["1", "2", "1", "S", "1", "2", "1"],
    8: ["1", "2", "1", "2", "2", "1", "2", "1"],
    9: ["1", "2", "1", "2", "S", "2", "1", "2", "1"],
    10: ["1", "2", "1", "2", "1", "1", "2", "1", "2", "1"],
    11: ["1", "2", "1", "2", "1", "S", "1", "2", "1", "2", "1"],
    12: ["1", "2", "1", "2", "1", "2", "2", "1", "2", "1", "2", "1"],
    13: ["1", "2", "1", "2", "1", "2", "S", "2", "1", "2", "1", "2", "1"],
    14: ["1", "2", "1", "2", "1", "2", "1", "1", "2", "1", "2", "1", "2", "1"],
    15: ["1", "2", "1", "2", "1", "2", "1", "S", "1", "2", "1", "2", "1", "2", "1"],
    16: ["1", "2", "1", "2", "1", "2", "1", "2", "2", "1", "2", "1", "2", "1", "2", "1"],
    17: ["1", "2", "1", "2", "1", "2", "1", "2", "S", "2", "1", "2", "1", "2", "1", "2", "1"],
    18: ["1", "2", "1", "2", "1", "2", "1", "2", "1", "1", "2", "1", "2", "1", "2", "1", "2", "1"],
}


def mania_sections(ini: SkinIni) -> list:
    """返回所有 [Mania] 区块（按顺序）。"""
    return ini.sections_named("Mania")


def find_mania_section(ini: SkinIni, keys: int) -> Optional[Section]:
    """按键数查找 [Mania] 区块。"""
    for sec in ini.sections_named("Mania"):
        if sec.get("Keys") == str(keys):
            return sec
    return None
