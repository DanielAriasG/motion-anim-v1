# Contrast table for a palette: which text colour (white or black) each fill supports, with WCAG ratios.
#   python contrast.py theme.js|motion.js        (reads `name: '#RRGGBB'` pairs)
# Thresholds (HIG accessibility): 4.5:1 for normal text, 3:1 for bold or large (>= 18 pt) text.
import re, sys, pathlib


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + .05) / (y + .05)


pairs = re.findall(r"(\w+)\s*:\s*'(#[0-9A-Fa-f]{6})'", pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
for name, h in pairs:
    w, b = ratio(h, '#FFFFFF'), ratio(h, '#000000')
    best, r = ('white', w) if w >= b else ('black', b)
    use = 'any text' if r >= 4.5 else 'bold/large text only' if r >= 3 else 'no text on it'
    print(f'{name:12s} {h}  fill: {best} text {r:4.1f}:1 ({use});  as text on white {w:4.1f}:1')
