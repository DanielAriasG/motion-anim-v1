# Builds a film end to end by running the services in services.json (narration -> timeline -> score -> mix ->
# video -> captions -> checks). Each service is one script that talks to the others only through files in the
# film folder; this orchestrator only decides which to run, in what order, and which can be skipped.
#   python make_film.py <film dir> [--voice elevenlabs|sapi|import:<folder>|keep|none] [--voice-id ID] [--out film.mp4]
#                       [--lufs -16] [--align auto|none] [--captions soft|none] [--bookends auto|none]
#                       [--music FILE] [--music-level -34]
#                       [--list] [--dry-run] [--only SERVICE ...] [--from SERVICE] [--force [SERVICE]]
#   --voice elevenlabs   ElevenLabs with word timestamps (needs ELEVENLABS_API_KEY in the environment)
#   --voice sapi         local Windows voice, for checking timing only
#   --voice import:DIR   any other source (Fish Audio, OpenAI, Azure, a recording): DIR holds <line id>.mp3|wav
#   --voice keep         reuse the voice already in <film>/vo (no new credits)
#   --voice none         a film without narration (timing from beats.js)
# Default: elevenlabs if narration.json exists and a key is set, else keep if vo/ exists, else none.
# With --voice-id the voice files are also kept in vo-<id>/ and reused on the next run.
# --align auto (default): estimated word timings are measured from the audio (align_whisper.py); a warning if
#   faster-whisper is missing. --captions soft (default when narrated): <out>.srt plus a subtitle track.
# --music FILE: a supplied music bed instead of the generated pad (music_file.py trims and fades it; score.js
#   still renders its accents, laid over the bed). --music-level: the bed's loudness, default -34 LUFS (15 LU
#   under the voice), ducked about 8 dB more under speech. Without --music the score.js pad is the music.
# --bookends auto (default): an intro or outro, when the film has one, is joined to the film (bookends.py):
#   built from a description (<film>/intro/ or <film>/outro/, made by new_film.py --intro-text/--outro-text,
#   built here first with the film's voice) or a clip the client supplied (<film>/bookends/intro.mp4,
#   outro.mp4). The captions run across all three. none: the film alone.
# Incremental: a service is skipped when its outputs are newer than its inputs and its command is unchanged
# (stamps in <film>/build/stamps.json), so changing film.js re-renders without touching the voice or the mix.
# --list shows the services; --dry-run shows the plan; --only runs just those services; --from starts the
# pipeline at one; --force reruns everything, or one service.
import argparse, fnmatch, glob, importlib.util, json, os, pathlib, shutil, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('film')
ap.add_argument('--voice'); ap.add_argument('--voice-id'); ap.add_argument('--out'); ap.add_argument('--lufs', default='-16')
ap.add_argument('--align', default='auto', choices=['auto', 'none']); ap.add_argument('--captions', default='soft', choices=['soft', 'none'])
ap.add_argument('--bookends', default='auto', choices=['auto', 'none'])
ap.add_argument('--music', help='a music file for the bed (else the generated pad in score.js)')
ap.add_argument('--music-level', default='-34', help='LUFS of a supplied music bed (default -34)')
ap.add_argument('--list', action='store_true'); ap.add_argument('--dry-run', action='store_true')
ap.add_argument('--only', nargs='+', default=[]); ap.add_argument('--from', dest='start')
ap.add_argument('--force', nargs='?', const='*', default=None)
a = ap.parse_args()

engine = pathlib.Path(__file__).resolve().parent
REG = json.loads((engine / 'services.json').read_text(encoding='utf-8'))
S = REG['services']
if a.list:
    for name, s in S.items():
        print(f'{name:16} {s["does"]}\n{"":16} in: {", ".join(s["in"]) or "-"}  ->  out: {", ".join(s["out"]) or "-"}')
    sys.exit(0)

film = pathlib.Path(a.film).resolve()
narrated = (film / 'narration.json').exists()
voice = a.voice or ('elevenlabs' if narrated and os.environ.get('ELEVENLABS_API_KEY') else 'keep' if (film / 'vo').exists() else 'none')
out = pathlib.Path(a.out).resolve() if a.out else film / f'{film.name}{"-" + a.voice_id if a.voice_id else ""}.mp4'
build = film / 'build'
V = {'film': film, 'engine': engine, 'build': build, 'project': film.parent, 'python': sys.executable, 'out': out,
     'video': build / f'{out.stem}.mp4', 'srt': out.with_suffix('.srt'), 'lufs': a.lufs, 'voice_id': a.voice_id or '',
     'voice_src': pathlib.Path(voice.split(':', 1)[1]).resolve() if voice.startswith('import:') else '',
     'music_src': pathlib.Path(a.music).resolve() if a.music else '', 'bed': 'bed.wav' if a.music else '', 'bed_lufs': a.music_level}

def scene_of(kind):    # an intro or outro built from a description: a small film folder of its own
    d = film / kind
    return d if (d / 'narration.json').exists() or (d / 'beats.js').exists() else None


ENDS = [k for k in ('intro', 'outro') if scene_of(k)]
supplied = (film / 'bookends').exists() and any((film / 'bookends').glob('*.*'))
bookends = a.bookends == 'auto' and bool(ENDS or supplied)
if bookends:    # the film's own captions go to build/; the delivered .srt (all three) is written by bookends.py
    V['srt'] = build / f'{out.stem}.srt' if narrated and voice != 'none' and a.captions == 'soft' else '-'
fill = lambda s: s.format(**{k: str(v) for k, v in V.items()})

# ---------- the pipeline for this film ----------
if narrated and voice != 'none':
    keep = film / f'vo-{a.voice_id}' if a.voice_id else None
    if keep and keep.exists():
        vsvc = ['voice-cache']
    elif voice in ('elevenlabs', 'sapi'):
        vsvc = [f'voice-{voice}']
    elif voice.startswith('import:'):
        vsvc = ['voice-import']
    elif voice == 'keep':
        vsvc = []
    else:
        sys.exit('unknown --voice ' + voice)
    plan = [x for p in REG['pipelines']['narrated'] for x in (vsvc if p == 'voice-*' else [p])]
    if a.align == 'none':
        plan.remove('align')
    if a.captions == 'none':
        plan = [x for x in plan if x not in ('captions', 'attach-captions')]
        plan.insert(plan.index('check'), 'deliver')
else:
    plan = list(REG['pipelines']['silent'])
if bookends:    # intro/outro scenes are built, then everything is joined: replaces attaching captions or delivering
    plan = [x for x in plan if x not in ('attach-captions', 'deliver')]
    plan[plan.index('check'):plan.index('check')] = ENDS + ['bookends']
if a.music:
    plan[plan.index('mix'):plan.index('mix')] = ['score-accents', 'music-file']
if a.start:
    plan = plan[plan.index(a.start):]
if a.only:
    plan = [x for x in plan if x in a.only] or a.only


def files(patterns):
    """(existing files, missing required patterns) for a service's in/out list"""
    found, missing = [], []
    for p in patterns:
        optional = p.endswith('?')
        p = fill(p.rstrip('?'))
        path = pathlib.Path(p) if pathlib.Path(p).is_absolute() else film / p
        hits = [pathlib.Path(h) for h in glob.glob(str(path))] if any(c in p for c in '*?[') else ([path] if path.exists() else [])
        hits = [h for h in hits if h.is_file()]
        found += hits
        if not hits and not optional:
            missing.append(p)
    return found, missing


def needs_ok(svc):
    lack = []
    for n in svc.get('needs', []):
        if n.startswith('env:'):
            ok = bool(os.environ.get(n[4:]))
        elif n.startswith('python:'):
            ok = importlib.util.find_spec(n[7:]) is not None
        elif ':' in n or n == 'chrome':
            ok = True    # checked by the service itself (puppeteer-core, the browser path)
        else:
            ok = shutil.which(n) is not None
        if not ok:
            lack.append(n)
    return lack


def absp(p):
    p = fill(p.rstrip('?'))
    return str(pathlib.Path(p) if pathlib.Path(p).is_absolute() else film / p)


dirty = set()    # outputs (as absolute patterns) that a service upstream has just changed, or is about to


def upstream_changed(svc):
    return [i for i in map(absp, svc['in']) if any(i == d or fnmatch.fnmatch(i, d) or fnmatch.fnmatch(d, i) for d in dirty)]


stamps_file = build / 'stamps.json'
stamps = json.loads(stamps_file.read_text(encoding='utf-8')) if stamps_file.exists() else {}


def decide(name, svc):
    """(run?, reason)"""
    cmd = ' '.join(fill(c) for c in svc.get('run', [name])) + json.dumps({k: fill(v) for k, v in svc.get('env', {}).items()})
    if a.only or a.force in ('*', name):
        return True, 'requested', cmd
    if svc.get('always'):
        return True, 'always runs (cheap when there is nothing to do)', cmd
    up = upstream_changed(svc)
    if up:
        return True, 'upstream changed: ' + ', '.join(pathlib.Path(u).name for u in up), cmd
    ins, missing_in = files(svc['in'])
    outs, missing_out = files(svc['out'])
    if missing_out:
        return True, 'output missing: ' + ', '.join(missing_out), cmd
    if stamps.get(name) != cmd:
        return True, 'command changed', cmd
    if ins and outs and max(f.stat().st_mtime for f in ins) > min(f.stat().st_mtime for f in outs):
        return True, 'inputs newer than outputs', cmd
    return False, 'up to date', cmd


def builtin(name):
    if name == 'voice-cache':
        shutil.rmtree(film / 'vo', ignore_errors=True)
        shutil.copytree(film / f'vo-{a.voice_id}', film / 'vo')
    elif name == 'deliver':
        shutil.copy2(V['video'], out)
    elif name in ('intro', 'outro'):    # a film of its own: same orchestrator, same voice and loudness
        sub = film / name
        v = (f'import:{V["voice_src"]}' if voice.startswith('import:') else voice) if (sub / 'narration.json').exists() else 'none'
        argv = [sys.executable, __file__, str(sub), '--voice', v, '--lufs', a.lufs, '--align', a.align, '--captions', a.captions,
                '--bookends', 'none'] + (['--voice-id', a.voice_id] if a.voice_id else []) + (['--force'] if a.force == '*' else [])
        print('>', ' '.join(argv), flush=True)
        if subprocess.run(argv).returncode:
            sys.exit(f'[{name}] failed: for an imported voice, put {name}.mp3 (its line) beside the film lines')


build.mkdir(exist_ok=True)
for name in plan:
    svc = S[name]
    go, why, cmd = decide(name, svc)
    print(f'[{name}] {"run" if go else "skip"}: {why}', flush=True)
    if not go:
        continue
    if a.dry_run:
        if not svc.get('always'):
            dirty.update(map(absp, svc['out']))
        continue
    before = {f: f.stat().st_mtime for f in files(svc['out'])[0]}
    lack = needs_ok(svc)
    if lack:
        msg = f'[{name}] missing {", ".join(lack)}'
        if svc.get('on_fail') == 'warn':
            print(msg + ' -> WARNING: ' + svc.get('warn', 'skipped'), flush=True)
            continue
        sys.exit(msg)
    if svc.get('builtin'):
        builtin(name)
    else:
        argv = [fill(c) for c in svc['run']]
        print('>', ' '.join(argv), flush=True)
        env = dict(os.environ, **{k: fill(v) for k, v in svc.get('env', {}).items() if fill(v)})
        r = subprocess.run(argv, env=env, cwd=fill(svc['cwd']) if 'cwd' in svc else None)
        if r.returncode:
            if svc.get('on_fail') == 'warn':
                print(f'[{name}] WARNING: {svc.get("warn", "failed")}', flush=True)
                continue
            sys.exit(f'[{name}] failed (exit {r.returncode})')
    after = {f: f.stat().st_mtime for f in files(svc['out'])[0]}
    if after != before:
        dirty.update(map(absp, svc['out']))
    stamps[name] = cmd
    stamps_file.write_text(json.dumps(stamps, indent=1), encoding='utf-8')
    # a saved voice follows its latest timings (after align, or after the voice service when align is off)
    if a.voice_id and (name == 'align' or (name.startswith('voice-') and name != 'voice-cache' and 'align' not in plan)):
        keep = film / f'vo-{a.voice_id}'
        shutil.rmtree(keep, ignore_errors=True); shutil.copytree(film / 'vo', keep)
if not a.dry_run:
    print('done:', out if out.exists() else '(no video yet)')
