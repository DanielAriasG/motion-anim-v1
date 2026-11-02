"""A music bed from a file the client supplies (instead of the generated pad): trimmed to the film, faded.
   python music_file.py <film dir> <music file> [bed.wav]
Length from cues.js (TOTAL) or beats.js (DURATION). The bed fades in over 2 s and out over the last 4 s; if the
file is shorter than the film it loops. mix.js sets its level (BED_LUFS, default -34: 15 LU under the voice) and
ducks it further while anyone speaks, and adds the score's accents (accents.wav) on top.
Check the licence of the file before delivery (royalty-free, attribution needed?) and say so in the report.
"""
import json, pathlib, re, subprocess, sys

film, src = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
out = film / (sys.argv[3] if len(sys.argv) > 3 else 'bed.wav')
if (film / 'cues.js').exists():
    total = json.loads(re.search(r'const CUES = (\{.*?\});', (film / 'cues.js').read_text(encoding='utf-8'), re.S).group(1))['TOTAL']
else:
    total = float(re.search(r'const DURATION\s*=\s*([\d.]+)', (film / 'beats.js').read_text(encoding='utf-8')).group(1))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-stream_loop', '-1', '-i', str(src), '-t', f'{total:.3f}',
                '-af', f'afade=t=in:d=2,afade=t=out:st={max(0, total - 4):.3f}:d=4',
                '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', str(out)], check=True)
print(f'bed {src.name} -> {out.name}, {total:.2f} s')
