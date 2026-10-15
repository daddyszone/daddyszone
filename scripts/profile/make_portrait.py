"""Build a detailed ASCII portrait from the saved public GitHub avatar."""
from collections import deque
from io import BytesIO
import json
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "profile"
ASSETS = ROOT / "assets" / "profile"
COLUMNS, ROWS = 144, 88
RAMP = " .,:;irsXA253hMHGS#9B&@"


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    source = DATA / "avatar-source.png"
    if not source.exists():
        req = Request("https://avatars.githubusercontent.com/u/182599669?v=4&s=1024", headers={"User-Agent": "daddyszone-profile-art"})
        with urlopen(req, timeout=30) as response:
            raw = response.read(8_000_001)
        if len(raw) > 8_000_000:
            raise ValueError("Avatar exceeds expected size")
        with Image.open(BytesIO(raw)) as original:
            original.convert("RGB").save(source)

    image = Image.open(source).convert("L")
    image = ImageOps.fit(image, (800, 800), method=Image.Resampling.LANCZOS)
    # Remove the thin frame present in this manga-style avatar.
    image = image.crop((8, 8, 792, 792)).resize((800, 800), Image.Resampling.LANCZOS)
    pixels = image.load()
    background = Image.new("L", image.size, 255)
    mask = background.load()
    queue = deque()
    # Remove only light areas connected to the outer background.
    for i in range(800):
        for x, y in ((i, 0), (i, 799), (0, i), (799, i)):
            if pixels[x, y] >= 215 and mask[x, y]:
                mask[x, y] = 0
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < 800 and 0 <= ny < 800 and mask[nx,ny] and pixels[nx,ny] >= 215:
                mask[nx,ny] = 0
                queue.append((nx,ny))
    # The speech balloon is outside the portrait, at the top-right.
    ImageDraw.Draw(background).rectangle((608, 0, 799, 232), fill=0)
    image = ImageOps.autocontrast(image, cutoff=1)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=3))
    foreground = Image.new("L", image.size, 0)
    foreground.paste(image, mask=background)
    # Keep faint contour detail without turning the shirt into a solid white block.
    edges = foreground.filter(ImageFilter.FIND_EDGES)
    foreground = Image.blend(foreground, edges, .16)
    small = foreground.resize((COLUMNS, ROWS), Image.Resampling.LANCZOS)
    values = list(small.getdata())
    rows = []
    for y in range(ROWS):
        rows.append("".join(RAMP[min(len(RAMP)-1, round((max(0, v-12)/243)**.85*(len(RAMP)-1)))] for v in values[y*COLUMNS:(y+1)*COLUMNS]))
    assert len(rows) == ROWS and all(len(row) == COLUMNS for row in rows)
    assert sum(c != " " for row in rows for c in row) > 1500, "Portrait unexpectedly empty"
    (DATA / "portrait.json").write_text(json.dumps(rows, indent=2)+"\n", encoding="utf-8")

    # An exact character-grid preview for visual QA, also useful as a static fallback.
    preview = Image.new("RGB", (800, 800), "#0d1117")
    draw = ImageDraw.Draw(preview)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 8)
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char != " ":
                draw.text((28+x*744/COLUMNS, 28+y*744/ROWS), char, font=font, fill="#d8dee9")
    preview.save(ASSETS / "avatar-preview.png", optimize=True)
    print(f"Detailed portrait: {COLUMNS} columns x {ROWS} rows; source {source.name}")


if __name__ == "__main__":
    main()
