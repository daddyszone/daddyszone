"""Build a detailed ASCII portrait from the saved public GitHub avatar."""
from collections import deque
import argparse
from io import BytesIO
import json
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "profile"
ASSETS = ROOT / "assets" / "profile"
COLUMNS, ROWS = 224, 136
RAMP = " .:-=+*#%@"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="High-resolution portrait source; used only to generate characters")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    source = args.source or DATA / "avatar-source.png"
    if args.source and not source.is_file():
        raise FileNotFoundError(source)
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
    # Keep the largest foreground component (the person), removing the separate
    # speech balloon and background specks without cutting into the hair.
    seen = bytearray(800 * 800)
    largest = []
    for sy in range(800):
        for sx in range(800):
            index = sy * 800 + sx
            if seen[index] or not mask[sx, sy]:
                continue
            component = []
            queue = deque([(sx, sy)])
            seen[index] = 1
            while queue:
                x, y = queue.popleft()
                component.append((x, y))
                for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0 <= nx < 800 and 0 <= ny < 800:
                        index = ny * 800 + nx
                        if not seen[index] and mask[nx, ny]:
                            seen[index] = 1
                            queue.append((nx, ny))
            if len(component) > len(largest):
                largest = component
    if len(largest) < 50_000:
        raise ValueError("Could not isolate avatar subject")
    background = Image.new("L", image.size, 0)
    mask = background.load()
    for x, y in largest:
        mask[x, y] = 255
    image = ImageOps.autocontrast(image, cutoff=1)
    image = image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=135, threshold=3))
    foreground = Image.new("L", image.size, 0)
    foreground.paste(image, mask=background)
    # Tighter head-and-shoulders framing gives eyes and glasses more character cells.
    # Retain actual luminance: edge blending previously flattened facial shading.
    foreground = foreground.crop((96, 24, 720, 648))
    small = foreground.resize((COLUMNS, ROWS), Image.Resampling.LANCZOS)
    small = small.filter(ImageFilter.UnsharpMask(radius=.65, percent=160, threshold=3))
    values = list(small.get_flattened_data())
    rows = []
    tones = []
    for y in range(ROWS):
        line = values[y*COLUMNS:(y+1)*COLUMNS]
        rows.append("".join(RAMP[min(len(RAMP)-1, round((v/255)**.65*(len(RAMP)-1)))] for v in line))
        tones.append("".join(format(min(15, round((v/255)**.55*15)), 'x') for v in line))
    assert len(rows) == ROWS and all(len(row) == COLUMNS for row in rows)
    assert sum(c != " " for row in rows for c in row) > 1500, "Portrait unexpectedly empty"
    portrait = {"columns": COLUMNS, "rows": rows, "tones": tones}
    (DATA / "portrait.json").write_text(json.dumps(portrait, indent=2)+"\n", encoding="utf-8")

    print(f"Detailed portrait: {COLUMNS} columns x {ROWS} rows; source {source.name}")


if __name__ == "__main__":
    main()
