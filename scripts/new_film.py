# Creates a film folder from the template, with its own copy of the engine next to it.
#   python new_film.py <project dir> <film name> [--narrated] [--title "..."] [--theme theme.js] [--assets dir] [--update-engine]
#                      [--intro-text "..." [--intro-title "..."] | --intro-video FILE] [--outro-text "..." [--outro-title "..."] | --outro-video FILE]
# Bookends (ask the client in the brief): an intro and/or outro either built from a description or a clip they supply.
#   --intro-text: the intro's sentence (spoken in a narrated film, shown in a silent one); --intro-title: a title
#   shown large under it (end the sentence with it to have it spoken). Makes <film>/intro/ (scene.js, score.js,
#   narration.json or beats.js), built by make_film.py with the film's voice. Same for --outro-*.
#   --intro-video / --outro-video: the client's clip, copied to <film>/bookends/; joined as it is (scaled, levelled).
# Layout:
#   <project>/engine/       motion.js, render.js, audio-lib.js, narration tools, mix, review   (shared by films)
#   <project>/<film name>/  index.html, film.js, score.js, narration.json | beats.js, [theme.js, assets]
# The engine is copied, not linked, so a finished film keeps rendering the same way after the skill changes.
# Rendering needs puppeteer-core in the project: run `npm i puppeteer-core` in <project> once.
import argparse, json, pathlib, re, shutil

ap = argparse.ArgumentParser()
ap.add_argument('project'); ap.add_argument('name')
ap.add_argument('--narrated', action='store_true')
ap.add_argument('--title')
ap.add_argument('--theme', help='a theme.js that sets window.THEME (copied into the film)')
ap.add_argument('--assets', help='a folder copied into the film (logos, images the theme or film loads)')
ap.add_argument('--update-engine', action='store_true')
for k in ('intro', 'outro'):
    ap.add_argument(f'--{k}-text'); ap.add_argument(f'--{k}-title', default=''); ap.add_argument(f'--{k}-video')
a = ap.parse_args()

skill = pathlib.Path(__file__).resolve().parent.parent
proj, film = pathlib.Path(a.project).resolve(), pathlib.Path(a.project).resolve() / a.name
engine = proj / 'engine'
if a.update_engine or not engine.exists():
    engine.mkdir(parents=True, exist_ok=True)
    for f in (skill / 'scripts').iterdir():
        if f.is_file() and f.name != 'new_film.py':
            shutil.copy2(f, engine / f.name)
if film.exists():
    raise SystemExit(f'{film} exists; pick another name')
film.mkdir(parents=True)
tpl = skill / 'assets' / 'template'
title = a.title or a.name.replace('-', ' ').capitalize()
theme_tag = ''
if a.theme:
    shutil.copy2(a.theme, film / 'theme.js')
    theme_tag = '<script src="theme.js"></script>'
if a.assets:
    shutil.copytree(a.assets, film / pathlib.Path(a.assets).name)
timing_tag = '<script src="cues.js"></script>' if a.narrated else '<script src="beats.js"></script>'
for name in ['index.html', 'film.js', 'score.js', 'narration.json' if a.narrated else 'beats.js']:
    s = (tpl / name).read_text(encoding='utf-8')
    s = s.replace('__TITLE__', title).replace('__THEME__', theme_tag).replace('__TIMING__', timing_tag)
    (film / name).write_text(s, encoding='utf-8')
for kind in ('intro', 'outro'):
    text, ttl, clip = getattr(a, f'{kind}_text'), getattr(a, f'{kind}_title'), getattr(a, f'{kind}_video')
    if clip:
        (film / 'bookends').mkdir(exist_ok=True)
        shutil.copy2(clip, film / 'bookends' / f'{kind}{pathlib.Path(clip).suffix.lower()}')
    if not (text or ttl):
        continue
    d, btpl = film / kind, tpl / 'bookend'
    d.mkdir()
    timing = 'cues.js' if a.narrated else 'beats.js'
    for name in ['index.html', 'scene.js', 'score.js']:
        b = (btpl / name).read_text(encoding='utf-8')
        b = (b.replace('__KIND__', kind).replace('__TITLE__', title).replace('__THEME__', theme_tag)
             .replace('__TIMING__', timing).replace('__SENTENCE__', json.dumps(text or ''))
             .replace('__TITLE_STR__', json.dumps(ttl)))
        (d / name).write_text(b, encoding='utf-8')
    if a.narrated and text:
        (d / 'narration.json').write_text(json.dumps({'language': 'en', 'kind': kind, 'lines': [
            {'id': kind, 'text': text, 'gap': 1.0 if kind == 'intro' else .6, 'scene': kind}], 'tail': 2.4},
            indent=1, ensure_ascii=False), encoding='utf-8')
    else:    # silent: the words build at once and hold for their reading time
        n = len(re.findall(r'\S+', f'{text or ""} {ttl}'))
        dur = round(max(4.0, 1.9 + max(2.5, 1 + n / 3) + 1.0), 1)
        (d / 'beats.js').write_text(f'const BEATS = {{}};\nconst DURATION = {dur};\n'
            "if (typeof window !== 'undefined') { window.BEATS = BEATS; window.DURATION = DURATION; }\n"
            "if (typeof module !== 'undefined') module.exports = { BEATS, DURATION };\n", encoding='utf-8')
(film / 'plan.md').write_text(f'# {title}\n\n## Thesis\n\n## Beats\n\n## Review notes\n', encoding='utf-8')
print(f'film: {film}\nengine: {engine}')
if not (proj / 'node_modules' / 'puppeteer-core').exists():
    print(f'next: cd "{proj}" && npm i puppeteer-core')
