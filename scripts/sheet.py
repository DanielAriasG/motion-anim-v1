# Tiles stills 2x2 per sheet (960x540 each) for close review: python sheet.py <stills dir> <out prefix> t1 t2 ...
import sys
from PIL import Image, ImageDraw

d, out, ts = sys.argv[1], sys.argv[2], sys.argv[3:]
for s in range(0, len(ts), 4):
    g = Image.new('RGB', (1920, 1080), 'white')
    dr = ImageDraw.Draw(g)
    for k, t in enumerate(ts[s:s + 4]):
        x, y = (k % 2) * 960, (k // 2) * 540
        g.paste(Image.open(f'{d}/t_{t}.png').convert('RGB').resize((960, 540), Image.LANCZOS), (x, y))
        dr.rectangle([x, y + 520, x + 64, y + 540], fill='black')
        dr.text((x + 4, y + 524), t + 's', fill='white')
    g.save(f'{out}{s // 4 + 1}.png')
    print(f'{out}{s // 4 + 1}.png')
