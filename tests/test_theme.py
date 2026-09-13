"""Regression checks for glyph clipping, exports, readability, and launcher argv."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import render_rain as rain


def luminance(color):
    values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)


class ThemeTests(unittest.TestCase):
    def test_shipped_wallpapers_are_valid_4k_images(self):
        wallpapers = list((ROOT / "backgrounds").glob("*.jpg"))
        self.assertTrue(wallpapers)
        for path in wallpapers:
            with self.subTest(wallpaper=path.name), Image.open(path) as image:
                self.assertEqual(image.size, (3840, 2160))
                self.assertEqual(image.mode, "RGB")
                image.verify()

    @unittest.skipUnless(shutil.which("glslangValidator"), "glslangValidator is not installed")
    def test_phosphor_shader_compiles(self):
        with tempfile.TemporaryDirectory() as directory:
            shader = Path(directory) / "phosphor.frag"
            shader.write_text(
                "#version 330 core\nuniform vec3 iResolution;\nuniform sampler2D iChannel0;\nout vec4 color;\n"
                + (ROOT / "extras/phosphor.glsl").read_text()
                + "\nvoid main() { mainImage(color, gl_FragCoord.xy); }\n")
            result = subprocess.run(["glslangValidator", "-S", "frag", str(shader)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_glyph_ink_fits_without_touching_cell_edges(self):
        for cell in (8, 16, 24, 32, 48):
            for ch, surface in rain.cache_glyphs(cell).items():
                surface.flush()
                data, stride = bytes(surface.get_data()), surface.get_stride()
                pixels = [data[y * stride:y * stride + cell] for y in range(cell)]
                with self.subTest(cell=cell, glyph=ch):
                    self.assertTrue(any(any(row) for row in pixels), "empty glyph")
                    self.assertFalse(any(pixels[0]) or any(pixels[-1]), "vertical clipping")
                    self.assertFalse(any(row[0] or row[-1] for row in pixels), "horizontal clipping")

    def test_exports_are_repeatable_and_seed_changes_composition(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / f"{i}.png" for i in range(3)]
            for path, seed in zip(paths, (1999, 1999, 2000)):
                rain.render(path, width=320, height=180, seed=seed, cell=16)
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            self.assertNotEqual(paths[0].read_bytes(), paths[2].read_bytes())
            with Image.open(paths[0]) as image:
                self.assertEqual(image.size, (320, 180))

    def test_portrait_jpeg_and_mono_export(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "portrait.jpg"
            rain.render(path, width=180, height=320, palette_name="mono", cell=16)
            with Image.open(path) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(image.size, (180, 320))
                r, g, b = image.convert("RGB").split()
                self.assertIsNone(ImageChops.difference(r, g).getbbox())
                self.assertIsNone(ImageChops.difference(g, b).getbbox())

    def test_text_contrast_and_ansi_aliases(self):
        colors = tomllib.loads((ROOT / "colors.toml").read_text())
        for bg in ("background", "lighter_background"):
            for key in ("foreground", "muted", "red", "magenta"):
                self.assertGreaterEqual(contrast(colors[key], colors[bg]), 4.5, (key, bg))
        self.assertGreaterEqual(contrast(colors["selection_foreground"], colors["selection_background"]), 4.5)
        roles = ["background", "red", "green", "yellow", "blue", "magenta", "cyan", "foreground",
                 "muted", "bright_red", "bright_green", "bright_yellow", "bright_blue", "bright_magenta",
                 "bright_cyan", "bright_foreground"]
        for i, role in enumerate(roles):
            self.assertEqual(colors[f"color{i}"], colors[role])

    def test_shell_sections_are_valid_and_colors_stay_in_palette(self):
        colors = tomllib.loads((ROOT / "colors.toml").read_text())
        for path in ROOT.glob("shell.*.toml"):
            values = tomllib.loads(path.read_text())
            self.assertFalse(any(isinstance(value, dict) for value in values.values()), path.name)
            for key, value in values.items():
                if isinstance(value, str) and value.startswith("#"):
                    self.assertIn(value, colors.values(), (path.name, key))
        lock = tomllib.loads((ROOT / "shell.lock.toml").read_text())
        self.assertGreaterEqual(contrast(lock["placeholder"], lock["background"]), 4.5)

    def test_launcher_preserves_command_arguments_and_scopes_prompt(self):
        with tempfile.TemporaryDirectory(prefix="matrix test ") as directory:
            root = Path(directory)
            for terminal in ("ghostty", "foot"):
                stub = root / terminal
                stub.write_text(f"#!{sys.executable}\nimport os,sys,json\nprint(json.dumps([sys.argv[1:],os.environ.get('STARSHIP_CONFIG')]))\n")
                stub.chmod(0o755)
                command = ["printf", "%s", "hello space", "$(do-not-execute)"]
                env = dict(os.environ, PATH=f"{root}:{os.environ['PATH']}")
                result = subprocess.run([sys.executable, str(ROOT / "scripts/matrix-terminal"),
                                         "--terminal", terminal, "--", *command],
                                        env=env, capture_output=True, text=True, check=True)
                argv, prompt = json.loads(result.stdout)
                self.assertEqual(argv[-len(command):], command)
                self.assertEqual(prompt, str(ROOT / "extras/starship.toml"))

    def test_invalid_cli_values_fail_before_export(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "not-created"
            result = subprocess.run([sys.executable, str(ROOT / "scripts/render_rain.py"),
                                     str(output), "--density", "nan"], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
