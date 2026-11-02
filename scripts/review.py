# Review aids: a labelled contact sheet of stills, and an optional palette check.
#   python review.py <stills dir> <out prefix> [--palette-from theme.js|motion.js] [--ignore-after T] [--tol 14]
# contact.png: every still in time order, 8 per row, labelled with its time.
# Palette check: counts saturated pixels whose hue is not within --tol degrees of a palette colour (hex codes
# read from the given file). Grey, near-white and near-black pixels are ignored. --ignore-after skips an end
# card that carries third-party marks (e.g. the EU emblem) which are allowed to be off-palette.
import sys, pathlib, re, colorsys, argparse
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument('src')
ap.add_argument('out')
ap.add_argument('--palette-from')
ap.add_argument('--ignore-after', type=float, default=1e9)
ap.add_argument('--tol', type=float, default=14)
a = ap.parse_args()

files = sorted(pathlib.Path(a.src).glob('t_*.png'), key=lambda p: float(re.findall(r't_([\d.]+)\.png', p.name)[0]))
if not files:
    sys.exit('no t_*.png stills in ' + a.src)
hues = []
if a.palette_from:
    for h in re.findall(r'#([0-9A-Fa-f]{6})\b', pathlib.Path(a.palette_from).read_text(encoding='utf-8')):
        hh, s, v = colorsys.rgb_to_hsv(*(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)))
        if s >= .2 and v >= .2:
            hues.append(hh * 360)

TW, TH, COLS = 240, 135, 8
sheet = Image.new('RGB', (TW * COLS, TH * ((len(files) + COLS - 1) // COLS)), 'white')
d = ImageDraw.Draw(sheet)
report = []
for n, f in enumerate(files):
    im = Image.open(f).convert('RGB')
    x, y = (n % COLS) * TW, (n // COLS) * TH
    sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
    d.rectangle([x, y, x + 50, y + 14], fill='white')
    d.text((x + 2, y + 2), f.stem[2:] + 's', fill='black')
    t = float(f.stem[2:])
    if hues and t < a.ignore_after:
        bad = 0
        for (r, g, b) in im.resize((480, 270)).getdata():
            hh, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if s < .3 or v < .25:
                continue
            if min(min(abs(hh * 360 - h), 360 - abs(hh * 360 - h)) for h in hues) > a.tol:
                bad += 1
        if bad:
            report.append(f'{f.stem}: {bad} off-palette px')
sheet.save(a.out + 'contact.png')
print(f'{len(files)} stills -> {a.out}contact.png')
if hues:
    print('\n'.join(report) or f'palette: no off-palette pixels ({len(hues)} palette hues)')
