#!/usr/bin/env python3
"""Deterministic digital rain at the requested resolution.

Requires Python 3.11+, Pycairo, PyGObject, Pillow and Noto Sans CJK JP.
See --help for export options; no desktop settings are changed.
"""
from __future__ import annotations

import argparse
import io
import math
from pathlib import Path
import random

import cairo
import gi
from PIL import Image, ImageChops, ImageFilter

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

GLYPHS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝｰ0123456789"
FONT = "Noto Sans CJK JP"
PALETTES = {
    "matrix": {"bg": "020503", "head": "E8FFE8", "body": "57F07A", "trail": "38C85A"},
    "mono": {"bg": "050505", "head": "EFEFEF", "body": "BBBBBB", "trail": "676767"},
}


def hex_rgb(value: str) -> tuple[float, ...]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def glyph_layouts(cell: int, font_name: str = FONT):
    """Fit actual ink, including bearings, with a shared baseline and padding."""
    ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_A8, cell, cell))
    font = Pango.FontDescription(font_name)
    size = float(cell - 4)
    for _ in range(20):
        font.set_absolute_size(size * Pango.SCALE)
        layouts = []
        for ch in GLYPHS:
            layout = PangoCairo.create_layout(ctx)
            layout.set_font_description(font)
            layout.set_text(ch, -1)
            if layout.get_unknown_glyphs_count():
                raise ValueError(f"Font {font_name!r} cannot render {ch!r}; install Noto Sans CJK JP")
            ink, _ = layout.get_pixel_extents()
            layouts.append((ch, layout, ink))
        top = min(ink.y for _, _, ink in layouts)
        bottom = max(ink.y + ink.height for _, _, ink in layouts)
        extent = max(bottom - top, max(ink.width for _, _, ink in layouts))
        if extent <= cell - 4:
            y = (cell - (bottom - top)) / 2 - top
            return [(ch, layout, (cell - ink.width) / 2 - ink.x, y)
                    for ch, layout, ink in layouts]
        size *= (cell - 4) / extent * 0.98
    raise ValueError(f"Could not fit {font_name!r} into a {cell}px cell")


def cache_glyphs(cell: int, font_name: str = FONT) -> dict[str, cairo.ImageSurface]:
    cached = {}
    for ch, layout, x, y in glyph_layouts(cell, font_name):
        surf = cairo.ImageSurface(cairo.FORMAT_A8, cell, cell)
        ctx = cairo.Context(surf)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.move_to(x, y)
        PangoCairo.show_layout(ctx, layout)
        cached[ch] = surf
    return cached


def paint_glyph(ctx, glyph, x, y, rgb, alpha):
    ctx.set_source_rgba(*rgb, min(1, max(0, alpha)))
    ctx.mask_surface(glyph, x, y)


def layer(ctx, glow, cache, cell, rng, density, dim, palette, width, height, quiet):
    cols, rows = math.ceil(width / cell), math.ceil(height / cell)
    head, body, trail = (hex_rgb(palette[key]) for key in ("head", "body", "trail"))
    for col in range(cols):
        if rng.random() > density:
            continue
        x = col * cell + rng.randrange(max(1, cell // 4))
        head_row = rng.randint(0, rows + 12)
        length = rng.randint(12, max(16, min(65, rows)))
        strength = dim * rng.uniform(0.70, 1.0)
        for t in range(length):
            row = head_row - t
            if not 0 <= row < rows:
                continue
            glyph = cache[rng.choice(GLYPHS)]
            fade = (1 - t / length) ** 1.1
            # Leave room for an editor without carving out an empty rectangle.
            distance = ((x / width - 0.5) / 0.30) ** 2 + ((row * cell / height - 0.5) / 0.48) ** 2
            local_dim = strength * (1 - quiet * math.exp(-distance))
            if t == 0:
                rgb, alpha = head, local_dim * 0.95
            elif t < 4:
                rgb, alpha = body, local_dim * (0.88 - t * 0.08)
            else:
                rgb, alpha = trail, local_dim * fade * rng.uniform(0.55, 1.0)
            paint_glyph(ctx, glyph, x, row * cell, rgb, alpha)
            if t < 3:
                paint_glyph(glow, glyph, x, row * cell, rgb, alpha * 0.45)


def to_image(surface) -> Image.Image:
    buffer = io.BytesIO()
    surface.write_to_png(buffer)
    buffer.seek(0)
    return Image.open(buffer).convert("RGB")


def render(path: Path, *, width=3840, height=2160, seed=1999, cell=32,
           density=0.82, palette_name="matrix", quiet=0.28, font=FONT,
           scanlines=0.05, bloom=0.30):
    rng = random.Random(seed)
    palette = PALETTES[palette_name]
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    glow_surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    ctx, glow = cairo.Context(surface), cairo.Context(glow_surface)
    ctx.set_source_rgb(*hex_rgb(palette["bg"]))
    ctx.paint()
    # Smaller distant streams; larger, sparser foreground streams.
    for size, population, strength in [(max(8, cell // 2), 0.95, 0.30),
                                        (max(8, cell * 3 // 4), 0.85, 0.65),
                                        (cell, 0.70, 1.15)]:
        layer(ctx, glow, cache_glyphs(size, font), size, rng, density * population,
              strength, palette, width, height, quiet)
    image = to_image(surface)
    if bloom:
        halo = to_image(glow_surface).filter(ImageFilter.GaussianBlur(max(0.7, cell / 14)))
        halo = Image.blend(Image.new("RGB", image.size), halo, bloom)
        image = ImageChops.add(image, halo)
    finish = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
    finish_ctx = cairo.Context(finish)
    finish_ctx.set_source_rgb(1, 1, 1)
    finish_ctx.paint()
    finish_ctx.set_source_rgba(0, 0, 0, scanlines)
    for y in range(0, height, 3):
        finish_ctx.rectangle(0, y, width, 1)
    finish_ctx.fill()
    gradient = cairo.RadialGradient(width / 2, height / 2, min(width, height) * 0.25,
                                    width / 2, height / 2, math.hypot(width, height) / 2)
    gradient.add_color_stop_rgba(0, 0, 0, 0, 0)
    gradient.add_color_stop_rgba(1, 0, 0, 0, 0.48)
    finish_ctx.set_source(gradient)
    finish_ctx.paint()
    image = ImageChops.multiply(image, to_image(finish))
    if path.suffix.lower() == ".jpg":
        image.save(path, quality=95, subsampling=0, optimize=True)
    else:
        image.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path,
                        default=Path(__file__).resolve().parent.parent / "backgrounds")
    parser.add_argument("--width", type=int, default=3840)
    parser.add_argument("--height", type=int, default=2160)
    parser.add_argument("--seed", type=int, default=1999)
    parser.add_argument("--cell", type=int, default=32, help="foreground glyph cell size in pixels")
    parser.add_argument("--density", type=float, default=0.82)
    parser.add_argument("--quiet", type=float, default=0.28, help="center dimming, 0 to 1")
    parser.add_argument("--scanlines", type=float, default=0.05)
    parser.add_argument("--bloom", type=float, default=0.30)
    parser.add_argument("--font", default=FONT)
    parser.add_argument("--palette", choices=["both", *PALETTES], default="both")
    parser.add_argument("--format", choices=["jpg", "png"], default="jpg")
    args = parser.parse_args()
    if not (64 <= args.width <= 16384 and 64 <= args.height <= 16384):
        parser.error("width and height must be between 64 and 16384")
    if args.width * args.height > 40_000_000:
        parser.error("keep exports at or below 40 megapixels")
    if not 8 <= args.cell <= 128:
        parser.error("cell must be between 8 and 128")
    for key in ("density", "quiet", "scanlines", "bloom"):
        if not 0 <= getattr(args, key) <= 1:
            parser.error(f"{key} must be between 0 and 1")
    args.output.mkdir(parents=True, exist_ok=True)
    for name, stem in [("matrix", "1-falling-code"), ("mono", "2-mono-rain")]:
        if args.palette not in ("both", name):
            continue
        path = args.output / f"{stem}.{args.format}"
        render(path, width=args.width, height=args.height, seed=args.seed,
               cell=args.cell, density=args.density, quiet=args.quiet,
               palette_name=name, font=args.font, scanlines=args.scanlines, bloom=args.bloom)
        print(f"Wrote {path} ({args.width}×{args.height})")


if __name__ == "__main__":
    main()
