# Matrix

An Omarchy 4 (Quattro) theme for the 1999 film.

Phosphor green on void black. Olive lift in the shadows, not gray. The
accent is the rain: `#00FF41`. It is meant to sit with the digital-rain
lock screen, but it is a full desktop theme — bar, menus, terminals,
Neovim, VS Code, btop, Chromium, Hyprland borders, and the boot unlock.

## Install

Omarchy 4:

```sh
omarchy theme install https://github.com/<you>/omarchy-matrix-theme
```

Until this lives on GitHub, copy it into place and apply:

```sh
rsync -a --delete \
  --exclude .git --exclude scripts \
  ./omarchy-matrix-theme/ ~/.config/omarchy/themes/matrix/
omarchy theme set matrix
```

Backgrounds cycle with `Super + Ctrl + Space`.

## Palette

| Role | Hex | In the film |
| --- | --- | --- |
| Background | `#070B08` | The simulation's black, with a green lift |
| Accent | `#00FF41` | Digital rain |
| Foreground | `#B7E4B8` | Phosphor text |
| Muted | `#3D6B42` | Dim trails, comments |
| Selection | `#0D3B14` | Highlighted code |
| Red | `#B33A3A` | The pill, the alarm, ACCESS DENIED |
| Yellow | `#C6C84A` | Sickly fluorescent |
| Blue | `#3D6B7A` | A leak of the real world |

Syntax highlighting stays inside that world: greens, a brick red, a
steel blue. No magenta nightclub.

## Backgrounds

All eight are **3840×2160**.

1. **Falling code** — dense katakana rain, rendered, not painted
2. **Trace program** — more black between the streams
3. **Deeper down** — finer columns
4. **Green street** — empty city, rain, CRT color grade
5. **The office** — cubicles, CRTs, fluorescent
6. **Hotel corridor** — 1999 carpet, rain on the far window
7. **CRT glass** — phosphor on curved glass
8. **Wet rooftop** — water towers, green city

Rain wallpapers are drawn at native 4K from real halfwidth katakana
(`scripts/render_rain.py`, Cairo + Pango, Noto Sans CJK JP). The five
filmic stills are super-resolved from their 1280×720 masters with
Real-ESRGAN, then downsampled to 4K so the grain and 1999 grade stay,
without the softness of a stretch.

## Lock screen

This theme paints the shell lock chrome green. Pair it with the custom
**Rain** design from Lock Screen Explorer if you have that plugin:

```sh
omarchy-shell lock setDesign my-rain
```

The Rain design hardcodes the same phosphor green, so the lock stays
in-world even if you hop themes.

## What it themes

Omarchy generates the rest from `colors.toml` when the theme is applied:

- Omarchy shell (bar, menus, notifications, OSD, lock chrome)
- Alacritty, Foot, Ghostty, Kitty
- Neovim (Aether), Helix, VS Code, Obsidian
- btop, Chromium
- Hyprland active border
- Keyboard RGB (`00FF41`)
- Icons: `Yaru-olive-dark`

## License

MIT. The cinematic stills are original generations. The rain is original
code. The unlock mark is the Omarchy geometry recolored to phosphor green.
