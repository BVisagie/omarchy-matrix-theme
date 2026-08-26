# Matrix

An Omarchy 4 (Quattro) theme for the 1999 film.

Phosphor green on void black. Olive lift in the shadows, not gray. The
accent is CRT green (`#3CBF5C`), not laser lime — the lock-screen rain
can stay hotter; the desktop sits in the body of the stream.

## Install

Omarchy 4:

```sh
omarchy theme install https://github.com/BVisagie/omarchy-matrix-theme
```

Or *Install > Style > Theme* in the Omarchy menu (`Super + Space`) and paste that URL.

Backgrounds cycle with `Super + Ctrl + Space`.

## Palette

| Role | Hex | In the film |
| --- | --- | --- |
| Background | `#080C09` | The simulation's black, with a green lift |
| Accent | `#3CBF5C` | CRT phosphor, not the rain's white-hot head |
| Foreground | `#8BC98C` | Terminal text, the body of the stream |
| Muted | `#3A6840` | Dim trails, comments |
| Selection | `#143318` | Highlighted code |
| Red | `#A83A3A` | The pill, the alarm, ACCESS DENIED |
| Yellow | `#B8BA48` | Sickly fluorescent |
| Cyan | `#4BB56A` | Prompt, still in-world |

Syntax highlighting stays inside that world: phosphor greens, a brick
red, a little teal for directories and the prompt. No magenta nightclub.

## Backgrounds

All five are **3840×2160**.

1. **Mono rain** — white-phosphor CRT (default)
2. **Falling code** — the same rain in Matrix green
3. **Green street** — empty city, rain, CRT color grade
4. **The office** — cubicles, CRTs, fluorescent
5. **Hotel corridor** — 1999 carpet, rain on the far window

Rain wallpapers are drawn at native 4K from real halfwidth katakana
(`scripts/render_rain.py`, Cairo + Pango, Noto Sans CJK JP). The filmic
stills are super-resolved from their 1280×720 masters with Real-ESRGAN,
then downsampled to 4K.

## Lock screen

This theme paints the shell lock chrome green. Pair it with the custom
**Rain** design from Lock Screen Explorer if you have that plugin:

```sh
omarchy-shell lock setDesign my-rain
```

The Rain design hardcodes the hotter cascade green (`#00FF41`), so the
lock stays in-world even if you hop themes. The desktop uses the dimmer
CRT accent.

## What it themes

Omarchy generates the rest from `colors.toml` when the theme is applied:

- Omarchy shell (bar, menus, notifications, OSD, lock chrome)
- Alacritty, Foot, Ghostty, Kitty
- Neovim (Aether), Helix, VS Code, Obsidian
- btop, Chromium
- Hyprland active border
- Keyboard RGB (`3CBF5C`)
- Icons: `Yaru-olive-dark`

## License

MIT. The cinematic stills are original generations. The rain is original
code. The unlock mark is the Omarchy geometry recolored to phosphor green.
