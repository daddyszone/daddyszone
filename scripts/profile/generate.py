"""Generate self-contained profile SVGs; Python standard library only."""
from __future__ import annotations

import argparse
import base64
from datetime import date, datetime, timedelta, timezone
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
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


def faithful_portrait(rows, x, y, size):
    """Keep the actual artwork intact; ASCII is only the introductory transition."""
    original = base64.b64encode((DATA / "avatar-source.png").read_bytes()).decode("ascii")
    parts = ['''<style>
      .portrait-original{animation:portrait-resolve 2.8s ease-in-out both}
      .portrait-ascii{opacity:0;animation:ascii-intro 2.8s ease-in-out both}
      .portrait-scan{opacity:0;animation:portrait-scan 2.8s ease-in-out both}
      @keyframes portrait-resolve{0%,28%{opacity:0}100%{opacity:1}}
      @keyframes ascii-intro{0%,30%{opacity:1}100%{opacity:0}}
      @keyframes portrait-scan{0%,24%{opacity:0;transform:translateY(0)}35%{opacity:.65}90%{opacity:.5}100%{opacity:0;transform:translateY(var(--portrait-travel))}}
      @media(prefers-reduced-motion:reduce){.portrait-original{animation:none!important;opacity:1!important}.portrait-ascii,.portrait-scan{display:none!important}}
    </style>''',
             '<g class="portrait-ascii">']
    parts += portrait_lines(rows, x, y, size)
    parts += ['</g>', f'<defs><clipPath id="portrait-clip"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="14"/></clipPath></defs>',
              f'<g clip-path="url(#portrait-clip)"><image class="portrait-original" x="{x}" y="{y}" width="{size}" height="{size}" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{original}"/>',
              f'<rect class="portrait-scan" style="--portrait-travel:{size}px" x="{x}" y="{y}" width="{size}" height="2" fill="#a3e635"/></g>',
              f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="14" fill="none" stroke="#30363d"/>']
    return parts


def hero(config):
    rows = json.loads((DATA / "portrait.json").read_text(encoding="utf-8"))
    parts = frame(900, 650, f"{config['name']} - @{config['username']}. Original profile artwork with an animated ASCII introduction.")
    for x, color in [(26, "#ff5f57"), (44, "#febc2e"), (62, "#28c840")]:
        parts.append(f'<circle cx="{x}" cy="25" r="5" fill="{color}"/>')
    parts += [text(85, 30, f"{config['username']} / personal terminal", 12, MUTED),
              text(864, 30, "v1.2", 11, MUTED, 'text-anchor="end"'),
              '<path d="M1 49H899" stroke="#30363d"/>',
              text(30, 82, "$ render avatar --original", 12, GREEN)]
    parts += faithful_portrait(rows, 25, 111, 480)
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
    full = frame(800, 800, f"{config['name']}: original profile artwork with ASCII intro")
    full += faithful_portrait(rows, 24, 20, 752)
    save_svg("avatar.svg", full)


def heatmap(data):
    days = data["days"]
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    best = max(day["count"] for day in days)
    parts = frame(900, 348, f"Decorative all-green calendar for @{data['username']}. Colors do not encode activity. Real totals: {total} contributions; {active} active days.")
    parts += ['''<defs>
      <linearGradient id="beam"><stop stop-color="#a3e635" stop-opacity="0"/><stop offset=".94" stop-color="#a3e635" stop-opacity=".10"/><stop offset="1" stop-color="#d9f99d" stop-opacity=".65"/></linearGradient>
      <linearGradient id="trace"><stop stop-color="#79c0ff"/><stop offset=".5" stop-color="#a3e635"/><stop offset="1" stop-color="#c084fc"/></linearGradient>
      <radialGradient id="ambient"><stop stop-color="#23432b" stop-opacity=".35"/><stop offset="1" stop-color="#0d1117" stop-opacity="0"/></radialGradient>
      <clipPath id="grid-window"><rect x="58" y="113" width="797" height="111" rx="6"/></clipPath>
    </defs>
    <style>
      .cell-enter{transform-box:fill-box;transform-origin:center;animation:assemble .85s cubic-bezier(.16,1,.3,1) both;animation-delay:var(--delay)}
      .cell-wave{transform-box:fill-box;transform-origin:center;animation:ripple 9s ease-in-out infinite;animation-delay:var(--wave)}
      .active-halo{transform-box:fill-box;transform-origin:center;animation:halo 3.6s ease-out infinite;animation-delay:var(--wave);pointer-events:none}
      .scan{animation:scan 9s linear infinite;animation-delay:2.7s;opacity:0;pointer-events:none}
      .border-trace{stroke-dasharray:100 2360;animation:trace 13s linear infinite;pointer-events:none}
      .signal{animation:signal 3.6s ease-in-out infinite}
      .boot{animation:boot .8s both;animation-delay:2s}
      .cursor{animation:signal 2.4s ease-in-out infinite}
      @keyframes assemble{0%{opacity:0;transform:translate(var(--dx),var(--dy)) rotate(-100deg) scale(.12)}70%{opacity:1;transform:translate(0,0) rotate(6deg) scale(1.2)}100%{opacity:1;transform:none}}
      @keyframes ripple{0%,8%,100%{transform:none;fill:#238636}3%{transform:translateY(-3px) scale(1.16);fill:#a3e635}40%{fill:#39d353}70%{fill:#2ea043}}
      @keyframes halo{0%{opacity:.65;transform:scale(1)}65%,100%{opacity:0;transform:scale(2.1)}}
      @keyframes scan{0%{opacity:0;transform:translateX(-110px)}8%{opacity:1}85%{opacity:1}100%{opacity:0;transform:translateX(820px)}}
      @keyframes trace{to{stroke-dashoffset:-2460}}
      @keyframes signal{0%,100%{opacity:.4}50%{opacity:1}}
      @keyframes boot{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:none}}
      @media(prefers-reduced-motion:reduce){.cell-enter,.cell-wave,.boot,.signal,.cursor{animation:none!important;transform:none!important;opacity:1!important}.scan,.active-halo,.border-trace{display:none!important}}
    </style>
    <ellipse cx="650" cy="156" rx="290" ry="155" fill="url(#ambient)"/>
    <rect class="border-trace" x="2" y="2" width="896" height="344" rx="17" fill="none" stroke="url(#trace)" stroke-width="2"/>
    <path d="M30 69H870" stroke="#26303c"/>
    <circle class="signal" cx="35" cy="33" r="4" fill="#a3e635"/>
    ''', text(49, 37, "CONTRIBUTION // MATRIX", 13, GREEN),
              text(30, 57, "$ render calendar --all-green --animate", 11, MUTED),
              text(870, 36, "ACTIVITY / 02", 10, MUTED, 'text-anchor="end"'),
              text(870, 56, "DECORATIVE GRID / REAL TOTALS", 9, MUTED, 'text-anchor="end"')]
    first = date.fromisoformat(days[0]["date"])
    start = first - timedelta(days=(first.weekday()+1) % 7)
    previous_month = None
    for item in days:
        day = date.fromisoformat(item["date"])
        col, row = divmod((day-start).days, 7)
        x, y = 62 + col*15, 119 + row*15
        if day.month != previous_month and day.day <= 7 and col < 51:
            parts.append(text(x, 103, day.strftime("%b"), 10, MUTED))
            previous_month = day.month
        delay = col*.035 + row*.065
        dx = ((col*17 + row*7) % 49)-24
        dy = -22 - ((col*7 + row*11) % 35)
        parts.append(f'<g class="cell-enter" style="--delay:{delay:.3f}s;--dx:{dx}px;--dy:{dy}px">')
        parts.append(f'<rect class="cell-wave" data-date="{item["date"]}" style="--wave:{3+col*.11+row*.07:.3f}s" x="{x}" y="{y}" width="11" height="11" rx="3" fill="#238636"><title>{item["date"]}: {item["count"]} actual contributions; decorative green color</title></rect>')
        parts.append(f'<rect class="active-halo" style="--wave:{3+col*.11+row*.07:.3f}s" x="{x}" y="{y}" width="11" height="11" rx="3" fill="none" stroke="#39d353" stroke-width=".6"/>')
        parts.append('</g>')
    parts += ['<g clip-path="url(#grid-window)"><rect class="scan" x="58" y="113" width="100" height="111" fill="url(#beam)"/></g>']
    for row, label in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        parts.append(text(29, 128+row*15, label, 9, MUTED))
    parts += ['<path d="M30 246H870" stroke="#26303c"/>', '<g class="boot">',
              text(35, 278, f"{total:,}", 25, GREEN), text(35, 298, "REAL CONTRIBUTIONS", 9, MUTED),
              text(262, 278, active, 25, "#79c0ff"), text(262, 298, "ACTIVE DAYS", 9, MUTED),
              text(458, 278, best, 25, "#c084fc"), text(458, 298, "BEST DAY", 9, MUTED),
              '</g>', text(660, 276, "ALL-GREEN ANIMATION", 11, GREEN)]
    parts += [text(660, 297, "COLORS ARE DECORATIVE", 9, MUTED),
              text(30, 331, f"{days[0]['date']} / {days[-1]['date']}", 10, MUTED),
              '<rect class="cursor" x="235" y="323" width="6" height="9" fill="#a3e635"/>',
              text(870, 331, "SYNCED " + data["updated"], 10, MUTED, 'text-anchor="end"')]
    save_svg("contributions.svg", parts)


def fetch_calendar(username):
    request = Request(f"https://github.com/users/{username}/contributions", headers={"User-Agent": "github-profile-art", "Accept": "text/html"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except HTTPError as error:
            if error.code not in (500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        delay = (2, 5)[attempt]
        print(f"Calendar request temporarily failed; retrying in {delay}s", flush=True)
        time.sleep(delay)


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
            html = fetch_calendar(config["username"])
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

