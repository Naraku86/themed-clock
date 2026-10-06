# Themed Clock

[Español](README.es.md) · [All ten animated themes](docs/THEMES.md)

A responsive character clock with ten themed animations. Runs in a terminal,
uses Python's standard library, and needs no images or compilation.

![BLAME! clock and block megastructure](docs/previews/blame.gif)

## Start

Requires Linux, Python 3.10+, Make for installation, and a UTF-8 terminal with a
monospace font. Kitty is recommended for the original appearance; no Kitty graphics
protocol or Wayland dependency is required.

```sh
git clone https://github.com/Naraku86/themed-clock.git
cd themed-clock
make install
~/.local/bin/themed-clock --theme dune
```

Numbers grow in proportional steps, then stay centered. Seconds appear at the same
size when they fit; the date sits below without moving the clock. Animations adapt
to the current terminal size and reveal the live clock afterward.

`S` / `W`: animate · `R`: reload configuration · `Q` / `Esc`: quit.

## Configure and integrate

Use `--theme` to select a profile. Optional configuration lives at
`~/.config/themed-clock/config.ini` (or `$XDG_CONFIG_HOME/themed-clock/config.ini`).
Fonts, colors, effects and timing are configurable.

[Configuration and desktop integration](docs/CONFIGURATION.md) ·
[Theme previews](docs/THEMES.md) · [License and provenance](NOTICE.md)

## Development

`make test` checks all themes, size tiers, seconds, animation endpoints and a real
pseudo-terminal resize. Python code and comments are in English. `frame()` is separate
from terminal I/O, so future timers can reuse it.

MIT. Pomodoro, alarms and AI control are planned for a second phase; they are not
implemented in this release. GIFs are renderer demos, not desktop recordings.
