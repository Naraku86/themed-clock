# Configuration and integration

[Español](CONFIGURATION.es.md) · [README](../README.md)

## Configuration

The file is optional. From the project root, create your own copy (preserve any
existing configuration before copying):

```sh
mkdir -p ~/.config/themed-clock
cp config.ini.example ~/.config/themed-clock/config.ini
```

`--config PATH` selects another file; an explicitly missing file is an error.
`--theme NAME` overrides the file and is retained when pressing `R`. Invalid reloads
keep the previous valid settings and show a brief message. Unknown options in the
INI file are ignored; invalid supported values fail with a readable error.

| Option | Default | Meaning |
| --- | --- | --- |
| `theme` | `auto` | Profile name; auto uses a configured theme source, otherwise minimal. |
| `theme_file` | empty | Text file containing a theme name, or symlink to a theme directory. |
| `font` | `auto` | `compact`, `arrakis`, `megastructure`, `serif`. |
| `style` | `auto` | `blocks`, `light`, `ascii`; controls numeral fill characters. |
| `color` | `auto` | Theme accent or `#RRGGBB`; palette support depends on terminal. |
| `max_scale` | `3` | Maximum integer scale, clamped to 1–6. |
| `seconds_min_width` | `54` | Minimum columns for large seconds; detailed designs also need 78. |
| `blink_colon` | `yes` | Alternate visible/hidden separators each second; `no` keeps them fixed. |
| `animations` | `yes` | `yes` or `no`. |
| `animation` | `auto` | Theme effect, `none`, or an explicit effect listed below. |
| `animation_interval` | `180` | Seconds after one animation ends until the next starts. |
| `animation_duration` | `8` | Seconds per animation, clamped to 2–30. |
| `worm_min_width` | `64` | Minimum columns for the optional fixed worm only. |
| `worm_min_height` | `16` | Minimum rows for the optional fixed worm only. |

Explicit effects: `sandstorm`, `worm`, `construction`, `energy`, `data`, `forge`,
`orbits`, `hourglass`, `wired`, `magi`, `pulse`. `signal` is a compatibility alias
for construction. Sandstorm/worm require Dune; construction/signal require BLAME!.
`style=ascii` changes numerals only; animations still use Unicode.

## Responsive rules

Numbers use fixed proportional tiers of 5/10/15 rows (compact) or 7/14/21 rows
(detailed), limited by both dimensions and `max_scale`. Detailed designs need at
least 50 columns and seven rows. Large seconds need 54 columns compact or 78 detailed;
otherwise they disappear. The date needs a blank row below the centered numbers.
Tiny terminals use a plain HH:MM line. Actual typeface and transparency belong to
the terminal emulator; the program controls the character drawing.

## Follow a desktop theme

`theme=auto` checks `THEMED_CLOCK_THEME`, then `theme_file`, then falls back to minimal.
Environment variables are inherited at startup; use a file or symlink for live theme
changes. A text file should contain a profile name, for example `blame`.

For Edgar-style dotfiles, set `theme_file=~/.config/temas-terminal/actual`.
The directory symlink is optional; no dotfiles are bundled. `fundacion` and
`mundodisco` are accepted as aliases for `foundation` and `discworld`.

## Start with the desktop

For Hyprland configurations using Lua:

```lua
hl.on("hyprland.start", function()
    hl.exec_cmd("kitty --class themed-clock -o window_padding_width=4 ~/.local/bin/themed-clock")
end)
```

For Sway:

```text
exec kitty --class themed-clock -o window_padding_width=4 ~/.local/bin/themed-clock
```

Adapt to your existing startup configuration. These follow the
[Hyprland example](https://github.com/hyprwm/Hyprland/blob/main/example/hyprland.lua)
and [Sway manual](https://github.com/swaywm/sway/blob/master/sway/sway.5.scd).
Floating rules, position, font size and opacity remain desktop/terminal settings.
No bar, wallpaper or terminal config is modified by installation.

## Test or preview

```sh
make test
~/.local/bin/themed-clock --theme foundation --preview 78 18 --animate
```

The first automatic animation starts after 20 seconds. `S`/`W` starts it immediately.
`Q`/`Esc`/`Ctrl+C` restores the terminal and exits. If Unicode characters look uneven,
use a suitable monospace font or try `style=ascii` with `animation=none`.

## Regenerate GIFs

Optional development tools: Pillow plus a Unicode monospace font. Run
`python3 scripts/render_previews.py --font /path/to/font.ttf`; omitting `--font` uses
Fontconfig's `fc-match monospace`. None of these are runtime dependencies.
