from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance


FRAME_COUNT = 12
SIZE = (1280, 480)
OUTPUT_PATH = Path("assets/cyberpunk-banner.gif")


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    source_w, source_h = image.size
    source_ratio = source_w / source_h
    target_ratio = target_w / target_h

    if source_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * source_ratio)
    else:
        new_w = target_w
        new_h = int(new_w / source_ratio)

    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def add_scanlines(image: Image.Image) -> Image.Image:
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    width, height = image.size

    for y in range(0, height, 4):
        alpha = 28 if (y // 4) % 2 == 0 else 18
        draw.line([(0, y), (width, y)], fill=(5, 12, 22, alpha), width=1)

    return Image.alpha_composite(image.convert("RGBA"), overlay)


def add_grid(draw: ImageDraw.ImageDraw, size: tuple[int, int], offset: int) -> None:
    width, height = size
    horizon = int(height * 0.72)

    for x in range(-width, width * 2, 80):
        px = x + offset
        draw.line([(px, horizon), (px + 160, height)], fill=(0, 255, 248, 22), width=2)

    for step in range(1, 7):
        y = horizon + int((height - horizon) * (step / 6))
        draw.line([(0, y), (width, y)], fill=(255, 46, 153, 16), width=2)


def add_hud(draw: ImageDraw.ImageDraw, size: tuple[int, int], tick: int) -> None:
    width, height = size
    pulse = 70 + int(55 * math.sin((tick / FRAME_COUNT) * math.tau))
    accent = 75 + int(45 * math.cos((tick / FRAME_COUNT) * math.tau))

    draw.rounded_rectangle(
        (28, 26, width - 28, height - 26),
        radius=26,
        outline=(0, 247, 255, pulse),
        width=3,
    )
    draw.rounded_rectangle(
        (40, 38, width - 40, height - 38),
        radius=20,
        outline=(255, 43, 214, accent),
        width=1,
    )

    corner = [
        ((56, 56), (132, 56), (56, 132)),
        ((width - 56, 56), (width - 132, 56), (width - 56, 132)),
        ((56, height - 56), (132, height - 56), (56, height - 132)),
        ((width - 56, height - 56), (width - 132, height - 56), (width - 56, height - 132)),
    ]
    for a, b, c in corner:
        draw.line([a, b], fill=(0, 247, 255, 180), width=4)
        draw.line([a, c], fill=(0, 247, 255, 180), width=4)

    for index in range(6):
        x = width - 310 + index * 38
        top = 62 + (index % 2) * 12
        bottom = top + 26 + (tick % 3) * 3
        draw.line([(x, top), (x, bottom)], fill=(255, 46, 153, 140), width=4)

    for index in range(5):
        x = 78 + index * 56
        length = 20 + ((tick + index) % 4) * 8
        draw.line([(x, height - 72), (x + length, height - 72)], fill=(0, 247, 255, 150), width=3)


def add_sweep(draw: ImageDraw.ImageDraw, size: tuple[int, int], tick: int) -> None:
    width, height = size
    sweep_y = int(((height + 120) / FRAME_COUNT) * tick) - 60
    for spread, alpha in ((0, 70), (26, 34), (56, 18)):
        draw.rectangle(
            (0, sweep_y - spread, width, sweep_y + spread),
            fill=(0, 247, 255, alpha),
        )


def build_frame(base: Image.Image, tick: int) -> Image.Image:
    frame = base.copy().convert("RGB")
    glow = 1 + 0.06 * math.sin((tick / FRAME_COUNT) * math.tau)
    frame = ImageEnhance.Brightness(frame).enhance(glow)
    frame = ImageEnhance.Contrast(frame).enhance(1.06)

    r, g, b = frame.split()
    offset = 2 if tick % 4 in (1, 2) else 0
    r = ImageChops.offset(r, -offset, 0)
    b = ImageChops.offset(b, offset, 0)
    frame = Image.merge("RGB", (r, g, b)).convert("RGBA")

    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    add_sweep(draw, frame.size, tick)
    add_grid(draw, frame.size, (tick * 22) % 80 - 40)
    add_hud(draw, frame.size, tick)

    for index in range(10):
        x = 72 + index * 118 + (tick * 7) % 118
        y = 92 + (index % 3) * 26
        draw.ellipse((x, y, x + 5, y + 5), fill=(0, 247, 255, 180))

    composite = Image.alpha_composite(frame, overlay)
    composite = add_scanlines(composite)
    return composite.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: build_cyberpunk_banner.py <input-image>")

    input_path = Path(sys.argv[1]).expanduser().resolve()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    source = Image.open(input_path).convert("RGB")
    base = fit_cover(source, SIZE)
    frames = [build_frame(base, tick) for tick in range(FRAME_COUNT)]

    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=90,
        loop=0,
        optimize=True,
        disposal=2,
    )

    print(OUTPUT_PATH.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
