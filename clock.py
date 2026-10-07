#!/usr/bin/env python3
"""Responsive character clock. Rendering stays independent of the time source."""
import argparse
import configparser
import curses
from datetime import datetime
import math
import os
import re
from pathlib import Path
import time

DIGITS = {
    '0': ('111', '101', '101', '101', '111'),
    '1': ('010', '110', '010', '010', '111'),
    '2': ('111', '001', '111', '100', '111'),
    '3': ('111', '001', '111', '001', '111'),
    '4': ('101', '101', '111', '001', '001'),
    '5': ('111', '100', '111', '001', '111'),
    '6': ('111', '100', '111', '101', '111'),
    '7': ('111', '001', '010', '010', '010'),
    '8': ('111', '101', '111', '101', '111'),
    '9': ('111', '101', '111', '001', '111'),
    ':': ('0', '1', '0', '1', '0'),
}
# Original geometric 5x7 digits: clipped corners and narrow inscription-like strokes.
ARRAKIS_DIGITS = {
    '0': ('01110', '10001', '10001', '10001', '10001', '10001', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('01110', '10001', '00001', '00110', '01000', '10000', '11111'),
    '3': ('11110', '00001', '00001', '01110', '00001', '00001', '11110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00010'),
    '5': ('11111', '10000', '10000', '11110', '00001', '00001', '11110'),
    '6': ('01110', '10000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '00001', '00010', '00100', '01000', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00001', '01110'),
    ':': ('0', '1', '0', '0', '0', '1', '0'),
}
# Squared industrial 5x7 numerals for the megastructure terminal.
BLAME_DIGITS = {
    '0': ('11111', '10001', '10011', '10101', '11001', '10001', '11111'),
    '1': ('01100', '00100', '00100', '00100', '00100', '00100', '01110'),
    '2': ('11111', '00001', '00001', '11111', '10000', '10000', '11111'),
    '3': ('11111', '00001', '00001', '01111', '00001', '00001', '11111'),
    '4': ('10001', '10001', '10001', '11111', '00001', '00001', '00001'),
    '5': ('11111', '10000', '10000', '11111', '00001', '00001', '11111'),
    '6': ('11111', '10000', '10000', '11111', '10001', '10001', '11111'),
    '7': ('11111', '00001', '00010', '00100', '00100', '00100', '00100'),
    '8': ('11111', '10001', '10001', '11111', '10001', '10001', '11111'),
    '9': ('11111', '10001', '10001', '11111', '00001', '00001', '11111'),
    ':': ('0', '1', '0', '0', '0', '1', '0'),
}
# Serif-like 5x7 numerals shared by the literary themes.
SERIF_DIGITS = {
    '0': ('01110', '11011', '10001', '10001', '10001', '11011', '01110'),
    '1': ('00100', '01100', '00100', '00100', '00100', '00100', '11111'),
    '2': ('01110', '10001', '00001', '00110', '01000', '10000', '11111'),
    '3': ('11110', '00001', '00001', '01110', '00001', '10001', '01110'),
    '4': ('00010', '00110', '01010', '10010', '11111', '00010', '00111'),
    '5': ('11111', '10000', '11110', '00001', '00001', '10001', '01110'),
    '6': ('00110', '01000', '10000', '11110', '10001', '10001', '01110'),
    '7': ('11111', '10001', '00010', '00100', '00100', '01000', '01000'),
    '8': ('01110', '10001', '10001', '01110', '10001', '10001', '01110'),
    '9': ('01110', '10001', '10001', '01111', '00001', '00010', '01100'),
    ':': ('0', '1', '0', '0', '0', '1', '0'),
}
# Reuse numeral families; theme identity also comes from palette and animation.
PROFILES = {
    'dune': ('arrakis', 'blocks', 'sandstorm', '#d9a55a'),
    'blame': ('megastructure', 'blocks', 'construction', '#8ba8bd'),
    'akira': ('megastructure', 'blocks', 'energy', '#e0261c'),
    'cyberpunk': ('megastructure', 'blocks', 'data', '#00e5ff'),
    'dwarven': ('serif', 'blocks', 'forge', '#c8963e'),
    'foundation': ('arrakis', 'blocks', 'orbits', '#7cc4ff'),
    'discworld': ('serif', 'blocks', 'hourglass', '#b07cff'),
    'lain': ('megastructure', 'light', 'wired', '#e58fa6'),
    'nerv': ('megastructure', 'blocks', 'magi', '#ef5350'),
    'minimal': ('compact', 'blocks', 'pulse', '#c5c5c8'),
}
SCENES = ('energy', 'data', 'forge', 'orbits', 'hourglass', 'wired', 'magi', 'pulse')
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'themed-clock/config.ini'
THEME_ALIASES = {'fundacion': 'foundation', 'mundodisco': 'discworld'}


def settings(path=CONFIG):
    parser = configparser.ConfigParser()
    if Path(path).exists():
        with Path(path).open(encoding='utf-8') as stream:
            parser.read_file(stream)
    section = parser['clock'] if parser.has_section('clock') else {}
    def number(key, default, low, high):
        value = float(section.get(key, default))
        if not math.isfinite(value):
            raise ValueError(f'{key} must be finite')
        return max(low, min(high, value))
    style = section.get('style', 'auto')
    if style not in ('auto', 'blocks', 'light', 'ascii'):
        raise ValueError('style must be auto, blocks, light or ascii')
    animation = section.get('animation', 'auto')
    if animation not in ('auto', 'none', 'sandstorm', 'worm', 'signal', 'construction') + SCENES:
        raise ValueError('Unknown animation; see README.md for supported names')
    font = section.get('font', 'auto')
    if font not in ('auto', 'compact', 'arrakis', 'megastructure', 'serif'):
        raise ValueError('font must be auto, compact, arrakis, megastructure or serif')
    theme = THEME_ALIASES.get(section.get('theme', 'auto'), section.get('theme', 'auto'))
    if theme != 'auto' and theme not in PROFILES:
        raise ValueError('Unknown theme')
    color = section.get('color', 'auto')
    if color != 'auto' and re.fullmatch(r'#[0-9a-fA-F]{6}', color) is None:
        raise ValueError('color must be auto or #RRGGBB')
    enabled = section.get('animations', 'yes').lower()
    if enabled not in ('yes', 'true', '1', 'no', 'false', '0'):
        raise ValueError('animations must be yes or no')
    blink_colon = parser.getboolean('clock', 'blink_colon', fallback=True)
    return dict(blink_colon=blink_colon, style=style, font=font, animation=animation, theme=theme, color=color,
                theme_file=section.get('theme_file', ''),
                animations=enabled in ('yes', 'true', '1'),
                max_scale=int(number('max_scale', 3, 1, 6)),
                seconds_width=int(number('seconds_min_width', 54, 27, 500)),
                interval=number('animation_interval', 180, 10, 86400),
                duration=number('animation_duration', 8, 2, 30),
                min_width=int(number('worm_min_width', 64, 40, 500)),
                min_height=int(number('worm_min_height', 16, 12, 200)))


def active_theme(config):
    if config['theme'] != 'auto':
        return config['theme']
    name = os.environ.get('THEMED_CLOCK_THEME', '')
    if not name and config['theme_file']:
        path = Path(config['theme_file']).expanduser()
        if path.is_symlink() or path.is_dir():
            name = path.resolve().name
        elif path.is_file():
            name = path.read_text(encoding='utf-8').strip()
    return THEME_ALIASES.get(name, name) if THEME_ALIASES.get(name, name) in PROFILES else 'minimal'


def animation_kind(config):
    theme = active_theme(config)
    requested = config['animation']
    if requested == 'auto':
        return PROFILES[theme][2] if theme in PROFILES else None
    if requested in SCENES:
        return requested
    if requested in ('signal', 'construction') and theme == 'blame':
        return requested
    if requested in ('sandstorm', 'worm') and theme == 'dune':
        return requested
    return None


def animation_fits(width, height, config):
    """Full-canvas effects scale to any size; the fixed worm needs more room."""
    kind = animation_kind(config)
    if not config['animations'] or kind is None:
        return False
    if kind != 'worm':
        return width > 0 and height > 0
    return width >= config['min_width'] and height >= config['min_height']


def sandstorm(canvas, progress):
    """Sweep sand across the canvas, fully cover it, then reveal the clock."""
    height, width = len(canvas), len(canvas[0]) if canvas else 0
    progress = max(0.0, min(1.0, progress))
    if progress in (0.0, 1.0):
        return
    entering = progress < 0.45
    leaving = progress > 0.55
    travel = progress / 0.45 if entering else (progress - 0.55) / 0.45
    tick = int(progress * 120)
    for y, row in enumerate(canvas):
        curve = math.sin(y / max(1, height - 1) * math.pi * 1.5) * width * 0.09
        boundary = travel * (width * 1.2) - width * 0.1 + curve
        for x in range(width):
            covered = (x < boundary if entering else x >= boundary) if (entering or leaving) else True
            if covered:
                # Moving grain texture and layered dunes; never reuse the clock pixels.
                grain = (x * 37 + y * 71 + tick * 13) % 23
                dune = height * 0.58 + math.sin(x / max(1, width) * math.tau + progress * 3) * height * 0.12
                texture = ' .:·' if y < dune else '░░▒:'
                row[x] = texture[grain % len(texture)]
            elif entering and 0 < x - boundary < max(1, min(6, width // 12)) and (x + y + tick) % 5 == 0:
                row[x] = '·'


def build_megastructure(canvas, progress):
    """Grow block towers, then uncover the live clock."""
    if not canvas or progress <= 0 or progress >= 1:
        return
    height, width = len(canvas), len(canvas[0])
    scene = [[' '] * width for _ in range(height)]
    bay = max(4, min(12, width // 7))
    for x in range(width):
        tower, local = divmod(x, bay)
        fraction = .35 + ((tower * 7 + 3) % 11) / 20
        top = max(0, height - max(1, round(height * fraction)))
        if local < max(1, bay - 2):
            for y in range(top, height):
                edge = local in (0, bay - 3) or y == top
                window = local % 3 == 1 and (y - top) % 3 == 1
                scene[y][x] = '▓' if edge else ' ' if window else '▒'
    growth = min(1.0, progress / .4)
    reveal = max(0.0, (progress - .6) / .4)
    lower_boundary = height - math.ceil(growth * height)
    upper_boundary = int(reveal * height)
    for y in range(height):
        if y >= lower_boundary and y >= upper_boundary:
            canvas[y][:] = scene[y]


def themed_scene(canvas, progress, kind):
    """Character-only scenes, normalized to the terminal's current dimensions."""
    if not canvas or progress <= 0 or progress >= 1:
        return
    height, width = len(canvas), len(canvas[0])
    scene = [[' '] * width for _ in range(height)]
    tick = int(progress * 24)
    for y, row in enumerate(scene):
        v = (y + .5) / height * 2 - 1
        for x in range(width):
            u = (x + .5) / max(1, width) * 2 - 1
            radius = math.hypot(u, v)
            char = ' '
            if kind == 'energy':
                wave = .15 + progress * 1.25
                if abs(radius - wave) < max(.07, 1 / height):
                    char = '▓'
                elif v > .45 and x % max(3, width // 12) != 0:
                    char = '▒'
            elif kind == 'data':
                spacing = max(2, width // 18)
                head = (x * 7 + tick) % (height + 5)
                if x % spacing == 0 and 0 <= head - y < 5:
                    char = '01:+'[(x + y) % 4]
            elif kind == 'forge':
                if -.65 < u < .65 and .05 < v < .4:
                    char = '▓'
                elif abs(u) < .25 and .4 <= v < .8:
                    char = '▒'
                elif -.45 < u < .45 and v < 0 and (x * 13 + y * 7 - tick) % 17 < 2:
                    char = '*' if (x + y) % 2 else '·'
            elif kind == 'orbits':
                orbit = math.hypot(u, v * 1.6)
                if min(abs(orbit - ring) for ring in (.35, .75, 1.15)) < max(.035, 1 / height):
                    char = '·'
                angle = math.atan2(v * 1.6, u)
                if abs(orbit - .75) < .12 and abs(math.sin(angle - progress * math.tau)) < .12:
                    char = '●'
                elif (x * 31 + y * 19) % 131 == 0:
                    char = '+'
            elif kind == 'hourglass':
                edge = abs(v) * .65 + .05
                if abs(abs(u) - edge) < max(.04, 1 / max(1, width)) or (abs(v) > .88 and abs(u) < .7):
                    char = '▓'
                elif abs(u) < edge and v > .25 + progress * .4:
                    char = '░'
                elif abs(u) < .035 and (y + tick) % 3 == 0:
                    char = '·'
            elif kind == 'wired':
                bay, floor = max(5, width // 8), max(2, height // 5)
                vertical = (x + (y // floor) * 2) % bay == 0
                horizontal = y % floor == 0
                if vertical and horizontal:
                    char = 'o' if (x + tick) % 3 else '●'
                elif vertical:
                    char = '│'
                elif horizontal:
                    char = '─'
            elif kind == 'magi':
                edge = max(abs(u), abs(u * .5 + v * .866), abs(u * .5 - v * .866))
                if abs(edge - .75) < max(.06, 1 / height):
                    char = '▓'
                elif abs(v - math.sin(progress * math.pi) * .7) < 1 / height:
                    char = '─'
            elif kind == 'pulse':
                if abs(radius - (.2 + progress * .7)) < max(.03, 1 / height):
                    char = '·'
            row[x] = char
    if kind == 'magi' and width >= 4:
        start = (width - 4) // 2
        scene[height // 2][start:start + 4] = 'MAGI'
    growth = min(1.0, progress / .35)
    reveal = max(0.0, (progress - .65) / .35)
    for y in range(height):
        if height - math.ceil(growth * height) <= y and y >= int(reveal * height):
            canvas[y][:] = scene[y]


def frame(width, height, now, config, progress=None):
    """Return a clipped character canvas; no terminal or clock side effects."""
    canvas = [[' '] * width for _ in range(height)]
    def put(x, y, text):
        if 0 <= y < height:
            for offset, char in enumerate(text):
                if 0 <= x + offset < width:
                    canvas[y][x + offset] = char
    def center(y, text):
        put(max(0, (width - len(text)) // 2), y, text)
    font = config['font']
    if font == 'auto':
        font = PROFILES.get(active_theme(config), ('compact',))[0]
    detailed = font != 'compact'
    detailed = detailed and width >= 50 and height >= 7
    digits = {'megastructure': BLAME_DIGITS, 'arrakis': ARRAKIS_DIGITS, 'serif': SERIF_DIGITS}[font] if detailed else DIGITS
    glyph_height = 7 if detailed else 5
    seconds_minimum = 78 if detailed else 54
    large_seconds = width >= max(config['seconds_width'], seconds_minimum)
    label = now.strftime('%H:%M:%S' if large_seconds else '%H:%M')
    bitmap_width = sum(len(digits[digit][0]) + 1 for digit in label) - 1
    # Integer size tiers preserve glyph proportions; spare space stays around them.
    if width >= bitmap_width and height >= glyph_height:
        scale = min(config['max_scale'], width // (bitmap_width * 2), height // glyph_height)
        sx, sy = (scale * 2, scale) if scale else (1, 1)
        digit_height = glyph_height * sy
        x0 = (width - bitmap_width * sx) // 2
        y0 = (height - digit_height) // 2
        style = config['style']
        if style == 'auto':
            style = PROFILES.get(active_theme(config), ('compact', 'blocks'))[1]
        glyph = {'blocks': '█', 'light': '░', 'ascii': '#'}[style]
        column = 0
        for digit in label:
            if digit == ':' and config['blink_colon'] and now.second % 2:
                column += len(digits[digit][0]) + 1
                continue
            for row, pixels in enumerate(digits[digit]):
                y1, y2 = y0 + row * sy, y0 + (row + 1) * sy
                for offset, pixel in enumerate(pixels):
                    if pixel == '1':
                        x1 = x0 + (column + offset) * sx
                        x2 = x1 + sx
                        for y in range(y1, y2):
                            put(x1, y, glyph * (x2 - x1))
            column += len(digits[digit][0]) + 1
        if y0 + digit_height + 1 < height:
            text = now.strftime('%d / %m / %Y') if width >= 14 else ''
            center(y0 + digit_height + 1, text)
    else:
        compact = now.strftime('%H:%M')
        if config['blink_colon'] and now.second % 2:
            compact = compact.replace(':', ' ')
        center(height // 2, compact)
        if height >= 5 and width >= 10:
            center(height // 2 + 2, now.strftime('%d/%m/%Y'))
    if progress is not None and animation_fits(width, height, config):
        kind = animation_kind(config)
        if kind in ('signal', 'construction'):
            build_megastructure(canvas, progress)
        elif kind in SCENES:
            themed_scene(canvas, progress, kind)
        elif kind == 'sandstorm':
            sandstorm(canvas, progress)
        else:
            # Emerges from the right and crosses the time before leaving the left edge.
            x = round(width - progress * (width + 38))
            y = height // 2 - 3 + round(math.sin(progress * math.tau) * 2)
            for row in range(7):
                put(x, y + row, ' ' * 38)
            head = ('   .-----._', ' / /| |\\ \\`--.', '| < | | > |===',
                    '| < | | > |===', ' \\ \\| |/ /_.-\'', '   `-----\'')
            for row, line in enumerate(head):
                put(x, y + row, line)
            for segment in range(7):
                bx = x + 14 + segment * 3
                by = y + 2 + round(math.sin(progress * math.tau + segment / 2))
                put(bx, by, ')||')
                put(bx, by + 1, ')||')
            center(height - 2, '~  ~   ~  SHAI-HULUD  ~   ~  ~')
    return [''.join(row) for row in canvas]


def set_color(theme, requested="auto"):
    if not curses.has_colors():
        return 0
    curses.start_color()
    curses.use_default_colors()
    color = curses.COLOR_YELLOW if theme == 'dune' else curses.COLOR_CYAN
    if (theme in PROFILES or requested != 'auto') and curses.COLORS >= 256 and curses.can_change_color():
        try:
            hex_color = PROFILES[theme][3] if requested == 'auto' else requested
            rgb = tuple(int(hex_color[index:index + 2], 16) for index in (1, 3, 5))
            curses.init_color(240, *(round(channel * 1000 / 255) for channel in rgb))
            color = 240
        except curses.error:
            pass
    curses.init_pair(1, color, -1)
    return curses.color_pair(1)


def run(screen, config, load):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    next_animation = time.monotonic() + 20
    started = None
    theme = None
    color_key = None
    reload_error = None
    while True:
        stamp = time.monotonic()
        height, width = screen.getmaxyx()
        current = active_theme(config)
        if (current, config['color']) != color_key:
            color_key = (current, config['color'])
            theme, color = current, set_color(current, config['color'])
            started = None
        eligible = animation_fits(width, height, config)
        if eligible and started is None and stamp >= next_animation:
            started = stamp
        if started is not None and (not eligible or stamp - started >= config['duration']):
            started = None
            next_animation = stamp + config['interval']
        progress = None if started is None else (stamp - started) / config['duration']
        screen.erase()
        for row, line in enumerate(frame(width, height, datetime.now(), config, progress)):
            try:
                screen.addstr(row, 0, line, color)
            except curses.error:
                pass  # Resizing and the terminal's bottom-right cell can reject a write.
        if reload_error and time.monotonic() < reload_error[1]:
            try:
                screen.addstr(height - 1, 0, reload_error[0][:max(0, width - 1)], color)
            except curses.error:
                pass
        screen.refresh()
        until_second = max(1, round((1 - time.time() % 1) * 1000))
        screen.timeout(min(80, until_second) if started is not None else until_second)
        key = screen.getch()
        if key in (ord('q'), ord('Q'), 27):
            return
        if key in (ord('w'), ord('W'), ord('s'), ord('S')) and eligible:
            started = time.monotonic()
        if key in (ord('r'), ord('R')):
            try:
                config = load()
                reload_error = None
            except (OSError, ValueError, configparser.Error) as error:
                reload_error = (f'Config error: {error}', time.monotonic() + 4)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, help='Configuration file (XDG default)')
    parser.add_argument('--preview', nargs=2, type=int, metavar=('COLUMNS', 'ROWS'))
    parser.add_argument('--theme', choices=tuple(PROFILES), help='Override the theme for this run')
    parser.add_argument('--worm', '--animate', action='store_true', help='Include the current theme animation in a static preview')
    args = parser.parse_args()
    def load():
        if args.config is not None and not args.config.is_file():
            raise ValueError(f'Configuration file not found: {args.config}')
        config = settings(args.config or CONFIG)
        if args.theme:
            config['theme'] = args.theme
        return config
    try:
        config = load()
        if args.preview:
            width, height = args.preview
            if not (1 <= width <= 500 and 1 <= height <= 200):
                parser.error('Preview dimensions must be 1..500 columns and 1..200 rows')
            print('\n'.join(frame(width, height, datetime.now(), config, 0.5 if args.worm else None)))
        else:
            curses.wrapper(run, config, load)
    except (OSError, ValueError, configparser.Error, curses.error) as error:
        parser.exit(1, f'Clock error: {error}\n')
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
