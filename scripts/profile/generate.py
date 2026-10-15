"""Generate self-contained profile SVGs; Python standard library only."""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets" / "profile"
DATA = ROOT / "data" / "profile"
GREEN = "#a3e635"
MUTED = "#8b949e"
PALETTE = ["#1c2530", "#284630", "#3f723b", "#6da947", GREEN]


class CalendarParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cells = {}
        self.tips = {}
        self.tip_id = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-date" in attrs and "data-level" in attrs:
            day = date.fromisoformat(attrs["data-date"])
            level = int(attrs["data-level"])
            if level not in range(5):
                raise ValueError("Unknown contribution level")
            self.cells[attrs["id"]] = {"date": day.isoformat(), "level": level}
        if tag == "tool-tip" and attrs.get("for"):
            self.tip_id = attrs["for"]
            self.tips[self.tip_id] = ""

    def handle_data(self, data):
        if self.tip_id:
            self.tips[self.tip_id] += data

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.tip_id = None

    def days(self):
        result = []
        for key, cell in self.cells.items():
            tip = self.tips.get(key, "").strip()
            match = re.match(r"(No|[\d,]+) contributions?\b", tip)
            if not match:
                raise ValueError(f"Missing contribution count for {cell['date']}")
            count = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            if (count == 0) != (cell["level"] == 0):
                raise ValueError("Contribution count and color disagree")
            result.append({**cell, "count": count})
        result.sort(key=lambda item: item["date"])
        if not 350 <= len(result) <= 371:
            raise ValueError(f"Incomplete calendar: {len(result)} days")
        for left, right in zip(result, result[1:]):
            if date.fromisoformat(right["date"]) - date.fromisoformat(left["date"]) != timedelta(days=1):
                raise ValueError("Calendar has missing or duplicate dates")
        if abs((date.today() - date.fromisoformat(result[-1]["date"])).days) > 2:
            raise ValueError("Calendar is stale")
        return result


def text(x, y, value, size=14, color="#e6edf3", extra=""):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" {extra}>{escape(str(value))}</text>'


def frame(width, height, title):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
            f'<title id="title">{escape(title)}</title>',
            '<style>text{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.reveal{animation:reveal .6s both}@keyframes reveal{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}@media(prefers-reduced-motion:reduce){.reveal{animation:none!important}}</style>',
            f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="18" fill="#0d1117" stroke="#30363d"/>']


def save_svg(name, parts):
    value = "\n".join(parts + ["</svg>"]) + "\n"
    ET.fromstring(value)
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / name).write_text(value, encoding="utf-8")


def portrait_lines(rows, x, y, size):
    parts = []
    count = len(rows)
    columns = max(len(row) for row in rows)
    line_height = size / count
    font_size = size / columns / .602
    for i, row in enumerate(rows):
        delay = i * 1.9 / count
        parts.append(f'<g class="reveal" style="animation-delay:{delay:.3f}s">' + text(x, y+(i+1)*line_height, row, round(font_size, 3), "#d8dee9", f'xml:space="preserve" textLength="{size}" lengthAdjust="spacingAndGlyphs"') + '</g>')
    return parts


def hero(config):
    rows = json.loads((DATA / "portrait.json").read_text(encoding="utf-8"))
    parts = frame(900, 650, f"{config['name']} — @{config['username']}. Detailed animated ASCII avatar and profile card.")
    for x, color in [(26, "#ff5f57"), (44, "#febc2e"), (62, "#28c840")]:
        parts.append(f'<circle cx="{x}" cy="25" r="5" fill="{color}"/>')
    parts += [text(85, 30, f"{config['username']} / personal terminal", 12, MUTED),
              text(864, 30, "v1.1", 11, MUTED, 'text-anchor="end"'),
              '<path d="M1 49H899" stroke="#30363d"/>',
              text(30, 82, "$ cat avatar.ascii --detail", 12, GREEN)]
    parts += portrait_lines(rows, 25, 111, 480)
    parts += ['<path d="M529 98V600" stroke="#26303c"/>',
              text(552, 163, "$ whoami", 13, GREEN),
              text(552, 211, config["name"].upper(), 27),
              text(552, 240, "@"+config["username"], 15, MUTED),
              text(552, 285, "Build. Learn. Repeat.", 17, GREEN),
              '<path d="M552 308H866" stroke="#26303c"/>']
    for i, (key, value) in enumerate(config["info"]):
        parts += [f'<g class="reveal" style="animation-delay:{.5+i*.16}s">', text(552, 340+i*42, key, 10, "#79c0ff"), text(552, 357+i*42, value, 12), '</g>']
    parts += [text(552, 545, "$ explore --projects", 12, MUTED),
              '<rect class="reveal" style="animation-delay:1.9s" x="727" y="534" width="8" height="13" fill="#a3e635"/>',
              text(30, 627, "IDENTITY / 01", 10, MUTED), text(865, 627, "ALWAYS A WORK IN PROGRESS", 10, MUTED, 'text-anchor="end"')]
    save_svg("identity.svg", parts)
    full = frame(800, 800, f"{config['name']}: detailed 144-column ASCII avatar")
    full += portrait_lines(rows, 24, 20, 752)
    save_svg("avatar.svg", full)


def heatmap(data):
    days = data["days"]
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max(day["count"] for day in days)
    parts = frame(900, 276, f"@{data['username']}: {total} contributions across {len(days)} displayed days; {active} active days.")
    parts += [text(30, 35, "$ git log --last-year", 14, GREEN),
              text(870, 35, "ACTIVITY / 02", 10, MUTED, 'text-anchor="end"'),
              '<path d="M30 51H870" stroke="#26303c"/>']
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday()+1) % 7)
    previous_month = None
    for item in days:
        day = date.fromisoformat(item["date"])
        col, row = divmod((day-start).days, 7)
        x, y = 62 + col*15, 88 + row*15
        if day.month != previous_month and day.day <= 7 and col < 51:
            parts.append(text(x, 76, day.strftime("%b"), 10, MUTED))
            previous_month = day.month
        parts.append(f'<rect class="reveal" style="animation-delay:{col*.016+row*.025:.3f}s" x="{x}" y="{y}" width="11" height="11" rx="3" fill="{PALETTE[item["level"]]}"><title>{item["date"]}: {item["count"]} contributions</title></rect>')
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(text(29, 97+row*15, label, 9, MUTED))
    parts += [text(62, 216, f"{total:,}", 19, GREEN), text(113, 216, "contributions", 11, MUTED),
              text(298, 216, f"{active} active days", 12), text(488, 216, f"{best} best day", 12), text(699, 216, "Less", 9, MUTED)]
    for i, color in enumerate(PALETTE):
        parts.append(f'<rect x="{730+i*16}" y="206" width="11" height="11" rx="3" fill="{color}"/>')
    parts += [text(818, 216, "More", 9, MUTED),
              text(30, 253, f"{days[0]['date']} / {days[-1]['date']}  |  GitHub contribution calendar", 10, MUTED),
              text(870, 253, "Updated " + data["updated"], 10, MUTED, 'text-anchor="end"')]
    save_svg("contributions.svg", parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fetch", action="store_true")
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    config = json.loads((DATA / "profile.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", config["username"]):
        raise ValueError("Invalid GitHub username")
    if args.fetch or args.html:
        if args.html:
            html = args.html.read_text(encoding="utf-8")
        else:
            request = Request(f"https://github.com/users/{config['username']}/contributions", headers={"User-Agent": "github-profile-art", "Accept": "text/html"})
            with urlopen(request, timeout=30) as response:
                html = response.read().decode("utf-8")
        calendar = CalendarParser()
        calendar.feed(html)
        data = {"username": config["username"], "updated": datetime.now(timezone.utc).date().isoformat(), "days": calendar.days()}
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "contributions.json").write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
    else:
        data = json.loads((DATA / "contributions.json").read_text(encoding="utf-8"))
    hero(config)
    heatmap(data)
    print(f"Generated profile art: {len(data['days'])} calendar days, {sum(d['count'] for d in data['days'])} contributions")


if __name__ == "__main__":
    main()
