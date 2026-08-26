#!/usr/bin/env python3
"""Render 1999-style digital-rain wallpapers with real halfwidth katakana."""

from __future__ import annotations

import math
import os
import random
import sys

import cairo
import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

GLYPHS = (
    "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"
    "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ"
    "0123456789"
)

W, H = 2560, 1440
FONT = "Noto Sans CJK JP"


def hex_rgb(s: str) -> tuple[float, float, float]:
    s = s.lstrip("#")
    return tuple(int(s[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def cache_glyphs(cell: int) -> dict[str, cairo.ImageSurface]:
    cached = {}
    font = Pango.FontDescription(f"{FONT} {cell - 2}")
    for ch in dict.fromkeys(GLYPHS):
        surf = cairo.ImageSurface(cairo.FORMAT_A8, cell, cell)
        ctx = cairo.Context(surf)
        layout = PangoCairo.create_layout(ctx)
        layout.set_font_description(font)
        layout.set_text(ch, -1)
        ink, logical = layout.get_pixel_extents()
        x = max(0, (cell - logical.width) / 2)
        y = max(0, (cell - logical.height) / 2)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.move_to(x, y)
        PangoCairo.show_layout(ctx, layout)
        cached[ch] = surf
    return cached


def paint_glyph(ctx, cache, ch, x, y, rgb, alpha):
    surf = cache.get(ch)
    if surf is None or alpha <= 0:
        return
    ctx.save()
    ctx.set_source_rgba(rgb[0], rgb[1], rgb[2], max(0.0, min(1.0, alpha)))
    ctx.mask_surface(surf, x, y)
    ctx.restore()


def layer(ctx, cache, cell, rng, density, speed_bias, dim, head_boost):
    cols = math.ceil(W / cell)
    rows = math.ceil(H / cell)
    head = hex_rgb("E8FFE8")
    body = hex_rgb("00FF41")
    mid = hex_rgb("00B32C")
    dark = hex_rgb("003B00")
    for c in range(cols):
        if rng.random() > density:
            continue
        length = rng.randint(12, 38)
        head_row = rng.randint(-4, rows + 2)
        bright = rng.random() > 0.72
        x = c * cell
        for t in range(length):
            row = head_row - t
            if row < -1 or row > rows:
                continue
            ch = rng.choice(GLYPHS)
            fade = 1.0 - (t / length)
            if t == 0:
                rgb, a = head if bright else hex_rgb("C8FFC8"), 0.95 * dim * head_boost
            elif t == 1:
                rgb, a = body, 0.9 * dim
            elif fade > 0.55:
                rgb, a = mid, (0.35 + 0.55 * fade) * dim
            else:
                rgb, a = dark, (0.12 + 0.4 * fade) * dim
            paint_glyph(ctx, cache, ch, x, row * cell, rgb, a)


def scanlines(ctx, strength=0.14):
    ctx.set_source_rgba(0, 0, 0, strength)
    ctx.set_line_width(1)
    for y in range(0, H, 3):
        ctx.move_to(0, y)
        ctx.line_to(W, y)
        ctx.stroke()


def vignette(ctx):
    # radial darkening toward the edges
    pat = cairo.RadialGradient(W / 2, H / 2, min(W, H) * 0.28, W / 2, H / 2, max(W, H) * 0.72)
    pat.add_color_stop_rgba(0.0, 0, 0, 0, 0.0)
    pat.add_color_stop_rgba(0.7, 0, 0, 0, 0.18)
    pat.add_color_stop_rgba(1.0, 0, 0, 0, 0.62)
    ctx.set_source(pat)
    ctx.paint()


def render(path: str, seed: int, near_cell: int, density: float) -> None:
    rng = random.Random(seed)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*hex_rgb("020503"))
    ctx.paint()

    far_cell = near_cell + 8
    mid_cell = near_cell + 4
    far_cache = cache_glyphs(far_cell)
    mid_cache = cache_glyphs(mid_cell)
    near_cache = cache_glyphs(near_cell)

    layer(ctx, far_cache, far_cell, rng, density * 0.55, 0.4, 0.28, 0.7)
    layer(ctx, mid_cache, mid_cell, rng, density * 0.75, 0.7, 0.55, 0.9)
    layer(ctx, near_cache, near_cell, rng, density, 1.0, 1.0, 1.15)

    scanlines(ctx, 0.16)
    vignette(ctx)
    surf.write_to_png(path)
    print("wrote", path)


def main() -> None:
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "backgrounds")
    os.makedirs(out, exist_ok=True)
    jobs = [
        ("1-falling-code.png", 1999, 18, 0.92),
        ("2-trace-program.png", 3103, 20, 0.72),
        ("3-deeper-down.png", 101, 16, 0.98),
    ]
    for name, seed, cell, density in jobs:
        render(os.path.join(out, name), seed, cell, density)


if __name__ == "__main__":
    main()
