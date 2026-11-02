# Brings narration from any other source into the pipeline: Fish Audio (connector or API), OpenAI TTS,
# Azure, Google, Polly, a human recording... One audio file per narration line, named <line id>.<ext>.
#   python import_voice.py <film dir> <folder with s1.mp3, s2.wav, ...> [--engine fish]
# For each line in narration.json: converts to <film dir>/vo/<id>.wav (48 kHz mono) and writes <id>.json
# with word timings. If the folder also holds <id>.words.json ([{w, s, e}] in seconds, e.g. from Azure word
# boundaries, Polly speech marks or Whisper), those timings are used; otherwise align_estimate.py estimates them
# and align_whisper.py (run by make_film.py) replaces the estimate with timings measured from the audio.
import json, pathlib, subprocess, sys

film, src = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
engine = sys.argv[sys.argv.index('--engine') + 1] if '--engine' in sys.argv else 'imported'
here = pathlib.Path(__file__).parent
N = json.loads((film / 'narration.json').read_text(encoding='utf-8'))
out = film / 'vo'; out.mkdir(exist_ok=True)
for L in N['lines']:
    clips = [p for p in src.glob(L['id'] + '.*') if p.suffix.lower() in ('.mp3', '.wav', '.ogg', '.opus', '.m4a', '.flac', '.aac')]
    if not clips: sys.exit(f'missing audio for line {L["id"]} in {src}')
    wav = out / (L['id'] + '.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(clips[0]), '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s24le', str(wav)], check=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(wav)], capture_output=True, text=True).stdout)
    given = src / (L['id'] + '.words.json')
    if given.exists():
        words, how = json.loads(given.read_text(encoding='utf-8')), 'given'
    else:
        r = subprocess.run([sys.executable, str(here / 'align_estimate.py'), str(wav), L['text']], capture_output=True, text=True, check=True)
        words, how = json.loads(r.stdout)['words'], 'estimated'
    (out / (L['id'] + '.json')).write_text(json.dumps({'engine': engine, 'timing': how, 'dur': dur, 'words': words}, indent=1), encoding='utf-8')
    print(f'{L["id"]} {dur:.2f} s, {len(words)} words ({how} timings)')
