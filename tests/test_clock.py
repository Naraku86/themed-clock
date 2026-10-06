"""Check responsive layout, animation thresholds and real terminal resize."""
from datetime import datetime
import fcntl
import importlib.util
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import termios
import time
import tempfile

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('clock', root / 'clock.py')
clock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clock)
config = clock.settings(root / 'config.ini.example') | {'theme': 'dune', 'font': 'compact', 'style': 'blocks'}
now = datetime(2026, 10, 6, 14, 38, 7)
for width, height in ((1, 1), (8, 3), (33, 8), (72, 7), (40, 12), (72, 18), (160, 45)):
    plain = clock.frame(width, height, now, config)
    moving = clock.frame(width, height, now, config, .5)
    assert len(plain) == height and all(len(row) == width for row in plain)
    assert len(moving) == height and all(len(row) == width for row in moving)
    eligible = clock.animation_fits(width, height, config)
    assert (plain != moving) == eligible
    if width >= 5 and height < 5:
        assert '14:38' in '\n'.join(plain)
assert clock.frame(72, 18, now, config, .2) != clock.frame(72, 18, now, config, .7)
assert clock.frame(72, 18, now, config | {'animations': False}, .5) == clock.frame(72, 18, now, config)
def drawing(width, height, options=config):
    picture = clock.frame(width, height, now, options)
    glyph = {'blocks': '█', 'light': '░', 'ascii': '#'}[options['style']]
    rows = [line for line in picture if glyph in line]
    return rows

for width, height, expected_height in ((34, 5, 5), (72, 7, 5), (108, 12, 10), (162, 18, 15), (300, 80, 15)):
    rows = drawing(width, height)
    assert len(rows) == expected_height, (width, height)
    picture = clock.frame(width, height, now, config)
    indices = [index for index, line in enumerate(picture) if '█' in line]
    assert abs(indices[0] - (height - expected_height) // 2) <= 1
# The drawing stays identical between tier boundaries and beyond the size cap.
assert clock.frame(72, 7, now, config)[6].strip() == ''
assert now.strftime('%d / %m / %Y') in clock.frame(72, 9, now, config)[8]
for height in (7, 8, 9, 10, 12):
    rows = [index for index, line in enumerate(clock.frame(72, height, now, config)) if '█' in line]
    assert rows[0] == (height - len(rows)) // 2, 'Date must not shift the digits'
assert [row.strip() for row in drawing(72, 7)] == [row.strip() for row in drawing(90, 9)]
assert [row.strip() for row in drawing(162, 18)] == [row.strip() for row in drawing(300, 80)]
for style, glyph in (('blocks', '█'), ('light', '░'), ('ascii', '#')):
    options = config | {'style': style}
    narrow, wide = config['seconds_width'] - 1, config['seconds_width']
    later = now.replace(second=8)
    def digits(width, stamp):
        return [line for line in clock.frame(width, 7, stamp, options) if glyph in line]
    assert clock.frame(narrow, 7, now, options) == clock.frame(narrow, 7, later, options)
    assert clock.frame(12, 3, now, options) == clock.frame(12, 3, later, options)
    assert digits(narrow, now) == digits(narrow, later)
    assert digits(wide, now) != digits(wide, later)
arrakis = config | {'font': 'arrakis'}
for symbol, bitmap in clock.ARRAKIS_DIGITS.items():
    assert len(bitmap) == 7
    assert all(len(row) == (1 if symbol == ':' else 5) for row in bitmap)
    assert all(set(row) <= {'0', '1'} for row in bitmap)
for width, height, expected in ((50, 7, 7), (78, 7, 7), (156, 14, 14), (234, 21, 21), (300, 80, 21)):
    rows = drawing(width, height, arrakis)
    assert len(rows) == expected
    picture = clock.frame(width, height, now, arrakis)
    indices = [i for i, row in enumerate(picture) if '█' in row]
    assert indices[0] == (height - expected) // 2
assert clock.frame(50, 7, now, arrakis) == clock.frame(50, 7, now.replace(second=8), arrakis)
assert clock.frame(78, 7, now, arrakis) != clock.frame(78, 7, now.replace(second=8), arrakis)
assert clock.frame(40, 6, now, arrakis) == clock.frame(40, 6, now, config)
assert clock.frame(78, 9, now, arrakis | {'font': 'auto'}) == clock.frame(78, 9, now, arrakis)
for style, glyph in (('blocks', '█'), ('light', '░'), ('ascii', '#')):
    assert glyph in ''.join(clock.frame(78, 7, now, arrakis | {'style': style}))
storm = config | {'animation': 'sandstorm'}
plain = clock.frame(78, 18, now, storm)
assert clock.frame(78, 18, now, storm, 0) == plain
assert clock.frame(78, 18, now, storm, 1) == plain
covered = clock.frame(78, 18, now, storm, .5)
assert '█' not in ''.join(covered), 'Storm must erase the whole clock'
assert covered != plain and all(len(row) == 78 for row in covered)
assert clock.frame(78, 18, now, storm, .2) != clock.frame(78, 18, now, storm, .8)
for width, height in ((1, 1), (8, 3), (34, 5), (50, 7), (78, 14), (234, 40)):
    ordinary = clock.frame(width, height, now, storm)
    assert clock.animation_fits(width, height, storm)
    assert clock.frame(width, height, now, storm, .5) != ordinary
    assert clock.frame(width, height, now, storm, 0) == ordinary
    assert clock.frame(width, height, now, storm, 1) == ordinary
    assert '█' not in ''.join(clock.frame(width, height, now, storm, .5))
assert not clock.animation_fits(40, 7, storm | {'animation': 'worm'})
assert clock.frame(78, 18, now, storm | {'animation': 'worm'}, .5) != covered
blame = config | {'theme': 'blame', 'font': 'auto', 'animation': 'auto'}
assert clock.animation_kind(blame) == 'construction'
assert clock.animation_kind(config | {'animation': 'auto'}) == 'sandstorm'
assert clock.frame(78, 9, now, blame) != clock.frame(78, 9, now, arrakis)
for width, height in ((1, 1), (8, 3), (50, 7), (78, 18), (234, 40)):
    plain = clock.frame(width, height, now, blame)
    assert clock.frame(width, height, now, blame, 0) == plain
    assert clock.frame(width, height, now, blame, 1) == plain
    covered = clock.frame(width, height, now, blame, .5)
    assert covered != plain and '▓' in ''.join(covered)
    assert now.strftime('%d / %m / %Y') not in ''.join(covered)
    assert len(covered) == height and all(len(row) == width for row in covered)
assert clock.frame(78, 18, now, blame, .15) != clock.frame(78, 18, now, blame, .35)
assert clock.animation_kind(blame | {'theme': 'minimal'}) == 'pulse'
assert '█' not in ''.join(clock.frame(78, 18, now, blame, .5)), 'Scene should contain only megastructure blocks'
assert '█' not in ''.join(clock.frame(8, 3, now, blame, .5)), 'Small scenes use only towers'
for name, profile in clock.PROFILES.items():
    options = config | {'theme': name, 'font': 'auto', 'style': 'auto', 'animation': 'auto'}
    assert clock.animation_kind(options) == profile[2]
    for width, height in ((1, 1), (12, 3), (40, 7), (78, 18), (160, 40)):
        plain = clock.frame(width, height, now, options)
        for progress in (0, .2, .5, .8, 1):
            image = clock.frame(width, height, now, options, progress)
            assert len(image) == height and all(len(row) == width for row in image)
            if progress in (0, 1):
                assert image == plain
        assert clock.frame(width, height, now, options | {'animations': False}, .5) == plain
    assert clock.frame(78, 18, now, options, .5) != clock.frame(78, 18, now, options)
assert clock.animation_kind(config | {'animation': 'none'}) is None
with tempfile.TemporaryDirectory() as temporary:
    path = Path(temporary) / 'config.ini'
    for option in ('max_scale=nan', 'animation_duration=inf', 'color=red', 'animations=maybe', 'theme=unknown'):
        path.write_text('[clock]\n' + option, encoding='utf-8')
        try:
            clock.settings(path)
        except ValueError:
            pass
        else:
            raise AssertionError(f'Invalid settings accepted: {option}')
    source = Path(temporary) / 'theme'
    source.write_text('fundacion', encoding='utf-8')
    options = config | {'theme': 'auto', 'theme_file': str(source)}
    previous = os.environ.pop('THEMED_CLOCK_THEME', None)
    try:
        assert clock.active_theme(options) == 'foundation'
        source.write_text('mundodisco', encoding='utf-8')
        assert clock.active_theme(options) == 'discworld'
        os.environ['THEMED_CLOCK_THEME'] = 'nerv'
        assert clock.active_theme(options) == 'nerv'
    finally:
        os.environ.pop('THEMED_CLOCK_THEME', None)
        if previous is not None:
            os.environ['THEMED_CLOCK_THEME'] = previous
master, slave = pty.openpty()
def resize(rows, columns):
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', rows, columns, 0, 0))
resize(18, 72)
process = subprocess.Popen(['python3', str(root / 'clock.py'), '--config', str(root / 'config.ini.example'), '--theme', 'blame'], stdin=slave,
                           stdout=slave, stderr=slave, env=os.environ | {'TERM': 'xterm-256color'})
try:
    assert select.select([master], [], [], 3)[0], 'Clock did not render'
    output = os.read(master, 65536)
    resize(4, 12)
    os.write(master, b'w')
    time.sleep(.15)
    resize(24, 100)
    os.write(master, b'q')
    assert process.wait(timeout=4) == 0
finally:
    if process.poll() is None:
        process.kill()
        process.wait()
    os.close(master)
    os.close(slave)
print('Layout, worm thresholds, animation, terminal resize and clean exit passed.')
