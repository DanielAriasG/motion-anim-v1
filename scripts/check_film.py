"""Checks a finished film before delivery and prints one PASS / WARN / FAIL line per check.
   python check_film.py <film dir> [<film.mp4>] [--lufs -16]
Exit code 1 if anything FAILs. Quote its output in the report.
Checks:
  video      1920x1080, 60 fps, length = the film's TOTAL (cues.js) or DURATION (beats.js), frame count
  audio      an audio stream; integrated loudness within 1 LU of --lufs; true peak at or below -1 dBFS
  timings    narrated films: every line's word timings native, given or measured (not estimated)
  captions   narrated films: <film>.srt next to the MP4 and a subtitle stream in it; the captions read the
             narration word for word; at most two lines of 42 characters per caption; inside the film
  bookends   films with an intro or outro (<film>/intro, <film>/outro, <film>/bookends): the MP4 is the film
             joined with them (build/bookends.json), and its captions include theirs
  tail       narrated films (not a bookend): at least 3 s after the last word for the end card
  alpha      no element helper sets ctx.globalAlpha outright (it must multiply, *=), so cards fade with
             their content; the scene root (drawScene) and lines marked `// alpha-root` may set it
"""
import json, pathlib, re, subprocess, sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
lufs = float(sys.argv[sys.argv.index('--lufs') + 1]) if '--lufs' in sys.argv else -16.0
if '--lufs' in sys.argv:
    args.remove(sys.argv[sys.argv.index('--lufs') + 1])
film = pathlib.Path(args[0]).resolve()
mp4 = pathlib.Path(args[1]).resolve() if len(args) > 1 else film / f'{film.name}.mp4'
results = []


def report(status, name, detail):
    results.append(status)
    print(f'{status:4} {name:9} {detail}')


def js_object(path, name):
    """the JSON literal assigned to `const <name> =` in a generated .js file"""
    m = re.search(rf'const {name}\s*=\s*(\{{.*?\}});\s*\n', path.read_text(encoding='utf-8'), re.S)
    return json.loads(m.group(1)) if m else None


narrated = (film / 'narration.json').exists() and (film / 'cues.js').exists()
CUES = js_object(film / 'cues.js', 'CUES') if narrated else None
if CUES:
    total = CUES['TOTAL']
else:
    m = re.search(r'const DURATION\s*=\s*([\d.]+)', (film / 'beats.js').read_text(encoding='utf-8')) if (film / 'beats.js').exists() else None
    total = float(m.group(1)) if m else None
# a film joined with its intro and outro (bookends.py): the delivered MP4 is longer, and its captions start with
# the intro's
BOOK = None
if (film / 'build' / 'bookends.json').exists():
    BOOK = json.loads((film / 'build' / 'bookends.json').read_text(encoding='utf-8'))
    if BOOK.get('out') != mp4.name:
        BOOK = None
film_total = total
if BOOK:
    total = BOOK['total']

# ---------- video and audio ----------
if not mp4.exists():
    report('FAIL', 'video', f'{mp4} not found')
else:
    pr = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-show_entries',
                                    'stream=codec_type,codec_name,width,height,r_frame_rate,nb_read_packets:format=duration',
                                    '-of', 'json', str(mp4)], capture_output=True, text=True).stdout)
    streams = pr.get('streams', [])
    v = next((s for s in streams if s['codec_type'] == 'video'), None)
    dur = float(pr['format']['duration'])
    if not v:
        report('FAIL', 'video', 'no video stream')
    else:
        num, den = map(int, v['r_frame_rate'].split('/'))
        fps, frames = num / den, int(v.get('nb_read_packets', 0))
        ok = v['width'] == 1920 and v['height'] == 1080 and abs(fps - 60) < .01
        ok_len = total is None or abs(dur - total) < .1
        ok_frames = abs(frames - dur * fps) <= 2
        report('PASS' if ok and ok_len and ok_frames else 'FAIL', 'video',
               f'{v["width"]}x{v["height"]} {fps:g} fps, {dur:.2f} s (film {total} s), {frames} frames')
    if not any(s['codec_type'] == 'audio' for s in streams):
        report('FAIL', 'audio', 'no audio stream')
    else:
        out = subprocess.run(['ffmpeg', '-nostats', '-i', str(mp4), '-map', '0:a:0', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                             capture_output=True, text=True).stderr
        i = float(re.findall(r'I:\s+(-?[\d.]+) LUFS', out)[-1])
        pk = float(re.findall(r'Peak:\s+(-?[\d.]+) dBFS', out)[-1])
        report('PASS' if abs(i - lufs) <= 1 and pk <= -1 else 'FAIL', 'audio',
               f'{i:.1f} LUFS (target {lufs:g}), true peak {pk:.1f} dBFS')

# ---------- narration: timings, captions, tail ----------
if narrated:
    N = json.loads((film / 'narration.json').read_text(encoding='utf-8'))
    def ends(kind):    # a built bookend's narration (a supplied clip has no captions of its own)
        f = film / kind / 'narration.json'
        return json.loads(f.read_text(encoding='utf-8'))['lines'] if BOOK and BOOK[kind] and f.exists() and             str(BOOK.get(f'{kind}_src') or '').startswith('built') else []
    INTRO = {'lines': ends('intro')}; OUTRO = {'lines': ends('outro')}
    kinds = {}
    for L in N['lines']:
        d = json.loads((film / 'vo' / (L['id'] + '.json')).read_text(encoding='utf-8'))
        native = d.get('engine', '').startswith(('elevenlabs', 'sapi', 'azure', 'polly'))
        kinds[L['id']] = d.get('timing') or ('native' if native else 'measured' if d.get('engine', '').endswith('+whisper') else 'estimated')
    est = [k for k, v in kinds.items() if v == 'estimated']
    report('FAIL' if est else 'PASS', 'timings',
           f'estimated in {", ".join(est)}: run align_whisper.py, then build_timeline.js' if est
           else ', '.join(sorted(set(kinds.values()))) + f' ({len(kinds)} lines)')

    srt = mp4.with_suffix('.srt')
    if not srt.exists():
        report('FAIL', 'captions', f'{srt.name} not found (make_film.py --captions soft)')
    else:
        blocks = [b.split('\n') for b in srt.read_text(encoding='utf-8').strip().split('\n\n') if b.strip()]
        caps = [(b[1], b[2:]) for b in blocks if len(b) >= 3]
        norm = lambda s: re.findall(r"[\w'’-]+", s.lower())
        said = [w for L in INTRO['lines'] + N['lines'] + OUTRO['lines'] for w in norm(L['text'])]
        shown = [w for _, lines in caps for w in norm(' '.join(lines))]
        long_ = [l for _, lines in caps for l in lines if len(l) > 42]
        three = sum(len(lines) > 2 for _, lines in caps)
        sec = lambda s: sum(float(x) * f for x, f in zip(s.replace(',', '.').split(':'), (3600, 60, 1)))
        late = [t for t, _ in caps if total and sec(t.split(' --> ')[1]) > total + .01]
        track = mp4.exists() and any(s['codec_type'] == 'subtitle' for s in streams)
        problems = (['text differs from the narration'] if said != shown else []) + \
                   ([f'{len(long_)} lines over 42 characters'] if long_ else []) + \
                   ([f'{three} captions over two lines'] if three else []) + \
                   (['a caption ends after the film'] if late else []) + \
                   ([] if track else ['no subtitle stream in the MP4'])
        report('FAIL' if problems else 'PASS', 'captions',
               '; '.join(problems) if problems else f'{len(caps)} captions match the narration; subtitle track in the MP4')

    if N.get('kind') not in ('intro', 'outro'):
        last = max(w['e'] for L in CUES['lines'].values() for w in L['words'])
        report('PASS' if film_total - last >= 3 else 'WARN', 'tail',
               f'{film_total - last:.1f} s after the last word (the end card needs 4-6 s)')

# ---------- bookends: the intro and outro the brief asked for are in the MP4 ----------
wanted = [k for k in ('intro', 'outro') if (film / k).is_dir() or any((film / 'bookends').glob(f'{k}.*'))]     if film.name not in ('intro', 'outro') else []
if BOOK:
    miss = [k for k in wanted if not BOOK[k]]
    report('FAIL' if miss else 'PASS', 'bookends',
           f'missing {", ".join(miss)}' if miss else
           f'intro {BOOK["intro"]:.2f} s + film {BOOK["film"]:.2f} s + outro {BOOK["outro"]:.2f} s')
elif wanted:
    report('WARN', 'bookends', f'{mp4.name} is the film alone: make_film.py joins the {" and ".join(wanted)} unless --bookends none')

# ---------- alpha: helpers multiply, only the scene root sets ----------
hits = []
for js in sorted(film.glob('*.js')):
    if js.name in ('cues.js', 'beats.js', 'score.js'):
        continue
    fn = None
    for n, line in enumerate(js.read_text(encoding='utf-8').splitlines(), 1):
        m = re.match(r'\s*function\s+(\w+)', line)
        if m and not line.startswith((' ', '\t')):
            fn = m.group(1)
        if re.search(r'globalAlpha\s*=(?!=)', line) and 'alpha-root' not in line and fn != 'drawScene':
            if not re.search(r'globalAlpha\s*=\s*1\s*;', line):   # a reset to 1 after drawing is fine
                hits.append(f'{js.name}:{n} ({fn})')
report('FAIL' if hits else 'PASS', 'alpha',
       'sets ctx.globalAlpha outright (use *=, or the card pops in before its content): ' + ', '.join(hits[:8])
       + (' ...' if len(hits) > 8 else '') if hits else 'every helper multiplies its alpha')

sys.exit(1 if 'FAIL' in results else 0)
