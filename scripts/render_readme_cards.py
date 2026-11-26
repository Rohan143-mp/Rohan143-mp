"""Render animated SVG cards for the GitHub profile README.

Reads data/contributions.json (refreshed daily by a GitHub Action) and
assets/portrait.jpg, then writes cards/hero.svg, cards/tiles.svg and
cards/activity.svg.

Only features that work inside an <img> tag are used: an inline <style>
block with CSS keyframes and base64 data URIs. GitHub strips scripts.

Set STATIC=1 to render the final frame with no animation (for screenshots).
"""
import json
import os
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
PORTRAIT = ROOT / "assets" / "portrait.jpg"
OUT = ROOT / "cards"
STATIC = os.environ.get("STATIC") == "1"

BG = "#0b0f19"
INK = "#e6f7ff"
MUTED = "#7d8aa3"
ACCENT = "#00f7ff"
FONT = "ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace"

RAMP = " .:-=+*#%@"


def portrait_rows(cols=46, rows=34):
    """Turn the photo into ASCII rows. Terminal characters are about twice
    as tall as they are wide, so the vertical scale is halved."""
    img = ImageOps.autocontrast(Image.open(PORTRAIT).convert("L"), cutoff=2)
    w, h = img.size
    img = img.resize((cols, max(1, int(h / w * cols * 0.5))))
    out = []
    for y in range(img.height):
        line = ""
        for x in range(img.width):
            v = img.getpixel((x, y))
            line += RAMP[min(len(RAMP) - 1, int((255 - v) / 256 * len(RAMP)))]
        out.append(line.rstrip())
    return [r for r in out[:rows] if r.strip()]


def esc(text):
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def hero_svg(data):
    rows = portrait_rows()
    row_h = 9
    art_x, art_y = 600, 40
    lines = []
    for i, line in enumerate(rows):
        style = "" if STATIC else f' style="animation:fadein .4s {0.4 + i * 0.03:.2f}s both"'
        lines.append(f'<text x="{art_x}" y="{art_y + i * row_h}" class="art"{style}>{esc(line)}</text>')
    height = max(300, art_y + len(rows) * row_h + 20)
    anim = "" if STATIC else (
        ".name{animation:rise .8s .1s both}"
        ".sub{animation:rise .8s .4s both}"
        ".rule{transform-origin:left;transform-box:fill-box;animation:grow .9s .6s both}"
        ".cursor{animation:blink 1s steps(1) infinite}"
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}" viewBox="0 0 900 {height}">
<style>
text{{font-family:{FONT}}}
.name{{font-size:52px;font-weight:700;fill:{INK}}}
.sub{{font-size:18px;fill:{MUTED}}}
.accent{{fill:{ACCENT}}}
.art{{font-size:8px;fill:{ACCENT};opacity:.85;white-space:pre}}
.rule{{stroke:{ACCENT};stroke-width:1.5}}
@keyframes rise{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
@keyframes fadein{{from{{opacity:0}}to{{opacity:.85}}}}
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes blink{{50%{{opacity:0}}}}
{anim}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<rect width="900" height="{height}" rx="14" fill="{BG}"/>
<rect x="0.5" y="0.5" width="899" height="{height - 1}" rx="14" fill="none" stroke="#1d2a44"/>
<text class="sub" x="40" y="48">~/rohan $ whoami</text>
<text class="name" x="40" y="118">Rohan <tspan class="accent">Pednekar</tspan></text>
<line class="rule" x1="40" y1="140" x2="540" y2="140"/>
<text class="sub" x="40" y="176">BE IT student · Full-Stack · AI/ML</text>
<text class="sub" x="40" y="204">Converting real-world problems into</text>
<text class="sub" x="40" y="228">smart software from Navi Mumbai <tspan class="accent cursor">_</tspan></text>
{chr(10).join(lines)}
</svg>'''


def tiles_svg(data):
    tiles = data["tiles"]
    w, h, gap = 900, 170, 20
    tw = (w - gap * (len(tiles) - 1)) / len(tiles)
    parts = []
    for i, t in enumerate(tiles):
        x = i * (tw + gap)
        delay = 0 if STATIC else 0.2 * i
        style = "" if STATIC else f' style="animation:tile .7s {delay:.1f}s both"'
        parts.append(f'''<g transform="translate({x:.1f},0)"{style}>
  <rect width="{tw:.1f}" height="{h - 10}" rx="12" fill="#11182a" stroke="{t['color']}" stroke-opacity=".5"/>
  <text x="20" y="44" class="t" fill="{t['color']}">{esc(t['metric'])}</text>
  <text x="20" y="90" class="h">{esc(t['title'])}</text>
  <text x="20" y="118" class="s">{esc(t['sub'])}</text>
  <text x="20" y="146" class="a" fill="{t['color']}">open →</text>
</g>''')
    anim = "" if STATIC else "@keyframes tile{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
text{{font-family:{FONT}}}
.t{{font-size:12px;letter-spacing:2px}}
.h{{font-size:20px;font-weight:700;fill:{INK}}}
.s{{font-size:13px;fill:{MUTED}}}
.a{{font-size:13px}}
{anim}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
{chr(10).join(parts)}
</svg>'''


def activity_svg(data):
    months = data["months"]
    w, h = 900, 300
    base_y, top = 230, 80
    max_v = max(m["count"] for m in months) or 1
    bw = (w - 80) / len(months)
    best = max(range(len(months)), key=lambda i: months[i]["count"])
    parts = []
    for i, m in enumerate(months):
        bh = (m["count"] / max_v) * (base_y - top)
        x = 40 + i * bw + bw * 0.2
        bar_w = bw * 0.6
        color = ACCENT if i == best else "#1f3a5f"
        style = "" if STATIC else (
            f' style="transform-box:fill-box;transform-origin:bottom;'
            f'animation:grow-y .6s {0.4 + i * 0.06:.2f}s both"')
        parts.append(f'<rect x="{x:.1f}" y="{base_y - bh:.1f}" width="{bar_w:.1f}" '
                     f'height="{bh:.1f}" rx="3" fill="{color}"{style}/>')
        parts.append(f'<text x="{x + bar_w / 2:.1f}" y="{base_y + 20}" class="m" '
                     f'text-anchor="middle">{esc(m["label"])}</text>')
    stats = [
        (data["total_last_year"], "contributions"),
        (data["streak"], "day streak"),
        (data["active_days"], "active days"),
        (data["busiest_day"]["count"], "busiest day"),
    ]
    for i, (v, label) in enumerate(stats):
        x = 40 + i * 215
        parts.insert(0, f'<text x="{x}" y="50" class="v">{esc(v)}</text>'
                        f'<text x="{x}" y="72" class="l">{esc(label)}</text>')
    anim = "" if STATIC else "@keyframes grow-y{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
text{{font-family:{FONT}}}
.v{{font-size:30px;font-weight:700;fill:{ACCENT}}}
.l{{font-size:12px;fill:{MUTED};letter-spacing:1px}}
.m{{font-size:12px;fill:{MUTED}}}
{anim}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<rect width="{w}" height="{h}" rx="14" fill="{BG}"/>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="#1d2a44"/>
<line x1="40" y1="{base_y}" x2="{w - 40}" y2="{base_y}" stroke="#1d2a44"/>
{chr(10).join(parts)}
</svg>'''


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    (OUT / "hero.svg").write_text(hero_svg(data), encoding="utf-8")
    (OUT / "tiles.svg").write_text(tiles_svg(data), encoding="utf-8")
    (OUT / "activity.svg").write_text(activity_svg(data), encoding="utf-8")
    print("cards written to", OUT, "(static)" if STATIC else "(animated)")


if __name__ == "__main__":
    main()
