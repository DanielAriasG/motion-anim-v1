"""Joins intro + film + outro into the delivered MP4, with one caption track across all three.
   python bookends.py <film dir> <film video.mp4> <film captions.srt|-> <out.mp4> [--lufs -16]
Each bookend is either
  - built: <film>/intro/ or <film>/outro/ is a small film of its own (made from the client's description;
    make_film.py builds it first) -> <film>/intro/intro.mp4 and its captions intro.srt, or
  - supplied: a clip the client gave, copied by new_film.py to <film>/bookends/intro.<ext> or outro.<ext>.
A built bookend wins over a supplied one; a missing one is skipped.
Out: <out.mp4> (1920x1080, 60 fps, AAC) with a switchable subtitle track when there are captions, <out>.srt
(intro captions, the film's shifted by the intro, the outro's shifted by intro + film), and
<film>/build/bookends.json with the three lengths (check_film.py reads it).
Supplied clips are scaled and padded to 1920x1080 (never stretched), set to 60 fps, and their sound is brought
to the film's loudness (--lufs) so the joins neither jump nor drop; a clip without sound gets silence.
"""
import json, pathlib, re, subprocess, sys

args = list(sys.argv[1:])
lufs = float(args[args.index('--lufs') + 1]) if '--lufs' in args else -16.0
if '--lufs' in args:
    del args[args.index('--lufs'):args.index('--lufs') + 2]
film, video, film_srt, out = pathlib.Path(args[0]).resolve(), pathlib.Path(args[1]), args[2], pathlib.Path(args[3])
build = film / 'build'; build.mkdir(exist_ok=True)
CLIP = ('.mp4', '.mov', '.m4v', '.webm', '.mkv')


def bookend(kind):
    """(clip, captions or None, supplied?) for 'intro' or 'outro', or (None, None, False)"""
    built = film / kind / f'{kind}.mp4'
    if built.exists():
        srt = film / kind / f'{kind}.srt'
        return built, srt if srt.exists() else None, False
    given = sorted(p for p in (film / 'bookends').glob(f'{kind}.*') if p.suffix.lower() in CLIP) if (film / 'bookends').exists() else []
    return (given[0], None, True) if given else (None, None, False)


def dur(p):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)],
                                capture_output=True, text=True, check=True).stdout)


def has_audio(p):
    return 'audio' in subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', str(p)],
                                     capture_output=True, text=True).stdout


def loudness(p):
    s = subprocess.run(['ffmpeg', '-nostats', '-i', str(p), '-map', '0:a:0', '-af', 'ebur128', '-f', 'null', '-'],
                       capture_output=True, text=True).stderr
    return float(re.findall(r'I:\s+(-?[\d.]+) LUFS', s)[-1])


intro, intro_srt, intro_given = bookend('intro')
outro, outro_srt, outro_given = bookend('outro')
parts = [(p, g) for p, g in ((intro, intro_given), (video, False), (outro, outro_given)) if p]

# ---------- picture and sound: every part to 1080p60 yuv420p, 48 kHz stereo; supplied clips levelled ----------
fl, ins, n = [], [], len(parts)
for p, _ in parts:
    ins += ['-i', str(p)]
for i, (p, given) in enumerate(parts):
    fl.append(f'[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,'
              f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,fps=60,format=yuv420p,setsar=1[v{i}]')
    if has_audio(p):
        gain = f',volume={lufs - loudness(p):.2f}dB,alimiter=limit=0.84:level=false' if given else ''
        fl.append(f'[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo{gain}[a{i}]')
    else:
        ins += ['-f', 'lavfi', '-t', f'{dur(p):.3f}', '-i', 'anullsrc=r=48000:cl=stereo']
        fl.append(f'[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]'); n += 1
fl.append(''.join(f'[v{i}][a{i}]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=1:a=1[v][a]')
joined = build / f'{out.stem}.joined.mp4'
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', ';'.join(fl), '-map', '[v]', '-map', '[a]',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'animation', '-r', '60', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(joined)], check=True)

# ---------- captions: intro, film, outro, each shifted to where it plays ----------
ts = lambda s: sum(float(x) * f for x, f in zip(s.replace(',', '.').split(':'), (3600, 60, 1)))


def fmt(t):
    ms = round(t * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def blocks(path, shift):
    if not path or not pathlib.Path(path).exists():
        return []
    res = []
    for b in pathlib.Path(path).read_text(encoding='utf-8').strip().split('\n\n'):
        ls = b.strip().split('\n')
        if len(ls) >= 3 and ' --> ' in ls[1]:
            a, z = ls[1].split(' --> ')
            res.append((f'{fmt(ts(a) + shift)} --> {fmt(ts(z) + shift)}', ls[2:]))
    return res


L = {'intro': dur(intro) if intro else 0.0, 'film': dur(video), 'outro': dur(outro) if outro else 0.0}
caps = blocks(intro_srt, 0) + blocks(None if film_srt == '-' else film_srt, L['intro']) + \
       blocks(outro_srt, L['intro'] + L['film'])
srt = out.with_suffix('.srt')
if caps:
    srt.write_text('\n'.join(f'{i}\n{t}\n' + '\n'.join(ls) + '\n' for i, (t, ls) in enumerate(caps, 1)), encoding='utf-8')
    narr = film / 'narration.json'
    lang = json.loads(narr.read_text(encoding='utf-8')).get('language', 'en') if narr.exists() else 'en'
    iso = {'en': 'eng', 'es': 'spa', 'ca': 'cat', 'fr': 'fra', 'de': 'deu', 'it': 'ita', 'pt': 'por', 'nl': 'nld', 'pl': 'pol'}.get(lang, 'und')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(joined), '-i', str(srt), '-map', '0', '-map', '1', '-c', 'copy',
                    '-c:s', 'mov_text', '-metadata:s:s:0', f'language={iso}', str(out)], check=True)
    joined.unlink()
else:
    joined.replace(out)
L['total'] = round(sum(L.values()), 3)
src = lambda p, g: None if not p else ('supplied: ' if g else 'built: ') + str(p)
(build / 'bookends.json').write_text(json.dumps({**L, 'out': out.name, 'intro_src': src(intro, intro_given),
                                                 'outro_src': src(outro, outro_given)}, indent=1), encoding='utf-8')
print(f'{out.name}: intro {L["intro"]:.2f} s + film {L["film"]:.2f} s + outro {L["outro"]:.2f} s = {L["total"]:.2f} s, '
      f'{len(caps)} captions')
