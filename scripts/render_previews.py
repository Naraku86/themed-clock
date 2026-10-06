"""Render reproducible GIF demos; optional dependencies: Pillow and a monospace font."""
import argparse
from datetime import datetime, timedelta
import importlib.util
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('clock', ROOT / 'clock.py')
clock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font', help='Path to a Unicode monospace TTF font')
    args = parser.parse_args()
    try:
        from PIL import Image, ImageDraw, ImageFont
        font_path = args.font or subprocess.check_output(
            ['fc-match', '-f', '%{file}', 'monospace'], text=True).strip()
        font = ImageFont.truetype(font_path, 14)
        cell_width, cell_height = math.ceil(font.getlength('M')), 20
        width, height = 78, 18
        destination = ROOT / 'docs/previews'
        destination.mkdir(parents=True, exist_ok=True)
        for theme, profile in clock.PROFILES.items():
            config = clock.settings(ROOT / 'config.ini.example') | {'theme': theme}
            frames = []
            phases = [None] + [index / 24 for index in range(25)] + [None]
            for index, progress in enumerate(phases):
                image = Image.new('RGB', (width * cell_width + 24, height * cell_height + 24), '#0e0e10')
                draw = ImageDraw.Draw(image)
                now = datetime(2026, 10, 6, 14, 38, 7) + timedelta(seconds=index // 4)
                rows = clock.frame(width, height, now, config, progress)
                for y, row in enumerate(rows):
                    for x, char in enumerate(row):
                        if char != ' ':
                            draw.text((12 + x * cell_width, 12 + y * cell_height), char,
                                      font=font, fill=profile[3])
                frames.append(image)
            frames[0].save(destination / f'{theme}.gif', save_all=True,
                           append_images=frames[1:], loop=0,
                           duration=[1400] + [120] * 25 + [1400], optimize=False)
            print(f'Rendered {theme}')
    except (ImportError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Cannot render previews: {error}\n')


if __name__ == '__main__':
    main()
