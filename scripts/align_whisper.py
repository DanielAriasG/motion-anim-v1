"""Measures word timings from the narration audio with speech-to-text word timestamps (faster-whisper).
   python align_whisper.py <film dir> [--force] [--model small.en]
For each line whose vo/<id>.json timings were estimated (Fish Audio, OpenAI, recordings...): faster-whisper
transcribes vo/<id>.wav with word timestamps (the script as its prompt), the recognised words are aligned to
the script's words in order (difflib), and each script word takes the measured start/end. Words whisper merged
or missed (numbers it writes as digits, hyphenations) are spread over the gap between matched neighbours.
The script's spelling is kept; only s/e change. Lines with native timings (ElevenLabs, SAPI) or given ones
are skipped unless --force. The estimate is kept as vo-estimated/<id>.json; a line where under half the
words match keeps its estimate and is flagged.
Needs: pip install faster-whisper (the model downloads once, ~460 MB for small). Runs on CPU.
Language: narration.json "language" (default "en"); English uses small.en, other languages small.
"""
import difflib, json, pathlib, re, shutil, subprocess, sys

import numpy as np

try:
    from faster_whisper import WhisperModel
except ImportError:
    sys.exit('align_whisper: faster-whisper is not installed (pip install faster-whisper); timings stay estimated')

film = pathlib.Path(sys.argv[1])
force = '--force' in sys.argv
N = json.loads((film / 'narration.json').read_text(encoding='utf-8'))
lang = N.get('language', 'en')
model_name = sys.argv[sys.argv.index('--model') + 1] if '--model' in sys.argv else ('small.en' if lang == 'en' else 'small')
NATIVE = ('elevenlabs', 'sapi', 'sapi-draft', 'azure', 'polly')
NUM = {'0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five', '6': 'six', '7': 'seven',
       '8': 'eight', '9': 'nine', '10': 'ten'} if lang == 'en' else {}


def norm(w):
    w = re.sub(r'[^\w]', '', w.lower())
    return NUM.get(w, w)


def pcm(path):
    """16 kHz mono float32 via ffmpeg (faster-whisper's own decoder breaks when the installed PyAV is newer)"""
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', str(path), '-f', 'f32le', '-ac', '1', '-ar', '16000', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def align(script, heard, dur):
    """script [{w, s, e}], heard [(word, s, e)] -> script words with measured s/e, share of words matched"""
    sm = difflib.SequenceMatcher(None, [norm(w['w']) for w in script], [norm(h[0]) for h in heard], autojunk=False)
    t = [None] * len(script)
    for b in sm.get_matching_blocks():
        for k in range(b.size):
            t[b.a + k] = heard[b.b + k][1:]
    matched = sum(x is not None for x in t) / max(1, len(script))
    i = 0
    while i < len(t):                      # spread unmatched runs over the gap, by word length
        if t[i] is not None:
            i += 1
            continue
        j = i
        while j < len(t) and t[j] is None:
            j += 1
        lo = t[i - 1][1] if i else (heard[0][1] if heard else 0.0)
        hi = t[j][0] if j < len(t) else (heard[-1][2] if heard else dur)
        hi = max(hi, lo + .05 * (j - i))
        lens = [max(1, len(script[k]['w'])) for k in range(i, j)]
        acc = lo
        for k, L in zip(range(i, j), lens):
            d = (hi - lo) * L / sum(lens)
            t[k] = (acc, acc + d)
            acc += d
        i = j
    return [{'w': w['w'], 's': round(s, 3), 'e': round(e, 3)} for w, (s, e) in zip(script, t)], matched


model = None
keep = film / 'vo-estimated'
for L in N['lines']:
    js = film / 'vo' / (L['id'] + '.json')
    data = json.loads(js.read_text(encoding='utf-8'))
    timing = data.get('timing') or ('native' if data.get('engine', '').startswith(NATIVE) else 'estimated')
    if timing in ('native', 'given', 'measured') and not force:
        print(f'{L["id"]}: {timing} timings, kept')
        continue
    if model is None:
        model = WhisperModel(model_name, device='cpu', compute_type='int8')
    keep.mkdir(exist_ok=True)
    if not (keep / js.name).exists():
        shutil.copy(js, keep / js.name)
    script = json.loads((keep / js.name).read_text(encoding='utf-8'))['words']
    segs, _ = model.transcribe(pcm(js.with_suffix('.wav')), language=lang, word_timestamps=True, beam_size=5,
                               initial_prompt=' '.join(w['w'] for w in script), vad_filter=False)
    heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    words, matched = align(script, heard, data['dur'])
    if matched < .5:
        print(f'{L["id"]}: only {matched:.0%} of words matched, estimate kept. Heard: "{" ".join(h[0] for h in heard)}"')
        continue
    shift = max(abs(n['s'] - o['s']) for n, o in zip(words, script))
    data.update(words=words, timing='measured', aligner=f'faster-whisper {model_name}')
    js.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{L["id"]}: {matched:.0%} of words matched, largest correction {shift:.2f} s')
