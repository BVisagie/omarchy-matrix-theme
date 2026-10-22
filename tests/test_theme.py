"""Validate the installable theme, its artwork, and terminal launcher."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def luminance(color):
    values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return sum(v * w for v, w in zip(linear, (0.2126, 0.7152, 0.0722)))



def contrast(a, b):
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)



class ThemeTests(unittest.TestCase):
    def test_shipped_wallpapers_are_valid_4k_images(self):
        supported = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
        wallpapers = sorted(path for path in (ROOT / "backgrounds").iterdir()
                            if path.suffix.lower() in supported)
        self.assertEqual({path.name for path in wallpapers}, {
            "0-hotel-corridor.jpg", "3-green-street.jpg",
            "4-the-office.jpg", "6-after-hours.jpg",
        })
        # Omarchy sorts shipped images and selects the first unmatched entry.
        # Keep code rain outside this directory, including after a rebuild.
        self.assertEqual(wallpapers[0].name, "0-hotel-corridor.jpg")
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


    def test_shipped_artwork_matches_provenance(self):
        manifest = json.loads((ROOT / "PROVENANCE.json").read_text())
        self.assertEqual(manifest["default_background"], "backgrounds/0-hotel-corridor.jpg")
        self.assertEqual({item["path"] for item in manifest["wallpapers"]},
                         {str(p.relative_to(ROOT)) for p in (ROOT / "backgrounds").glob("*.jpg")})
        for item in [*manifest["wallpapers"], manifest["preview"]]:
            path = ROOT / item["path"]
            with self.subTest(path=item["path"]):
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
                with Image.open(path) as image:
                    self.assertEqual(list(image.size), item["dimensions"])
                    image.verify()

    def test_theme_download_budget(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/check-size")],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
