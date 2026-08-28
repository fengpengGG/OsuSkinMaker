# 临时查询脚本：从 osu_skin.db 提取目标元素的官方分类与图片属性
import sqlite3

DB = r"e:\trae\osuskin\.trae\skills\osu-skin-skills\assets\osu_skin.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

print("type:", [r[0] for r in c.execute("SELECT DISTINCT type FROM elements")])
print("client:", [r[0] for r in c.execute("SELECT DISTINCT client FROM elements")])
print("--- mode tables ---")
for r in c.execute(
    "SELECT id, filename, category, type, client FROM elements WHERE filename LIKE '%mode%' LIMIT 8"
):
    print(dict(r))

targets = [
    "mode-osu", "mode-osu-med", "mode-osu-small", "mode-taiko", "mode-taiko-med", "mode-taiko-small",
    "mode-fruits", "mode-fruits-med", "mode-fruits-small", "mode-mania", "mode-mania-med", "mode-mania-small",
    "selection-mode", "selection-mods", "selection-options", "selection-random", "selection-tab",
    "star", "star2", "songselect-bottom", "songselect-top", "menu-button-background", "menu-back",
    "taiko-barline", "taiko-drum-inner", "taiko-drum-outer", "taiko-glow", "taiko-roll-end", "taiko-roll-middle",
    "taiko-slider", "taiko-slider-fail", "taiko-pippidonidle", "taiko-pippidonfail", "taiko-pippidonkiai",
    "taiko-pippidonclear", "taiko-taikohitcircle", "taiko-taikohitcircleoverlay", "taiko-taikobigcircle",
    "taiko-taikobigcircleoverlay", "taiko-spinner-warning", "taiko-hit300g", "taiko-flower-group",
    "inputoverlay-background", "inputoverlay-key",
    "scoreentry-0", "scoreentry-1", "scoreentry-2", "scoreentry-3", "scoreentry-4",
    "scoreentry-5", "scoreentry-6", "scoreentry-7", "scoreentry-8", "scoreentry-9",
    "default-0", "default-1", "default-2", "default-3", "default-4",
    "default-5", "default-6", "default-7", "default-8", "default-9",
    "sliderendmiss", "slidertickmiss", "sliderpoint10", "sliderpoint30", "spinner-osu",
    "count1", "count2", "count3", "ready", "go",
    "arrow-pause", "arrow-warning", "play-warningarrow", "play-unranked", "section-pass", "section-fail",
    "multi-skipped", "masking-border", "button-left", "button-middle", "button-right", "cursor-ripple",
    "ranking-accuracy", "ranking-graph", "ranking-maxcombo", "ranking-panel", "ranking-perfect", "ranking-title",
    "ranking-winner", "pause-replay", "score-pp",
    "ranking-X-small", "ranking-XH-small", "ranking-S-small", "ranking-SH-small", "ranking-A-small",
    "ranking-B-small", "ranking-C-small", "ranking-D-small",
]

placeholders = ",".join("?" * len(targets))
rows = c.execute(
    """SELECT e.filename, e.category, e.subcategory, e.client, e.description,
              d.blend_mode, d.origin, d.suggested_size
       FROM elements e LEFT JOIN image_details d ON d.element_id = e.id
       WHERE e.id IN (""" + placeholders + """) AND e.type='image'""",
    targets,
).fetchall()

found = {r["filename"] for r in rows}
missing = sorted(set(t for t in targets if t not in found))
print("=== 命中 %d 项 / 未命中 %d 项 ===" % (len(rows), len(missing)))
for t in missing:
    print(f"[MISS] {t}")
print("=== 命中明细 ===")
for r in rows:
    print("|".join([
        r["filename"], r["category"] or "", r["subcategory"] or "", r["client"] or "",
        r["blend_mode"] or "", r["origin"] or "", r["suggested_size"] or "",
        (r["description"] or "").replace("|", "/"),
    ]))