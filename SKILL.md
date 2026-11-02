---
name: motion-anim-v1
description: 'Motion Anim V1 - makes motion-graphics videos (explainers, animated diagrams, kinetic type, product or concept films) as code-rendered 1080p60 MP4s with Apple Human Interface Guidelines design craft, an optional AI narration whose words drive every animation (ElevenLabs, Fish Audio, OpenAI, Azure, Polly or free local voices, word timings measured from the audio), captions, a generated score or the client''s own music, optional intro and outro, and a loudness-normalised mix. Use it whenever someone asks for an animated or motion video, an explainer film, a narrated or voice-over video, an animation synced to speech, a branded video from their brand guide and logos, or wants to turn a script, slides or a concept into a video, even if they do not say motion graphics. For eCAN Plus branded films use eCAN Motion Anim V1 instead.'
---

# Motion Anim V1

Code-rendered motion films: every frame is drawn on a canvas by a pure function of time, rendered with
headless Chrome and encoded by ffmpeg. That makes films exact, repeatable and easy to re-time, and lets a
narration drive the animation word by word.

Design follows Apple's Human Interface Guidelines translated to film (references/design.md): one idea per
film, one signature moment, one colour per meaning, the system typeface, calm spring motion, nothing moving
through readable text. The default look is Apple's light system palette; the client's brand is swapped in
with a theme file.

## What you need
Node 18+, Python 3 with Pillow, ffmpeg/ffprobe on PATH, Chrome or Edge, and `npm i puppeteer-core` in the
project folder (new_film.py tells you). Narration is optional and needs a voice service
(references/narration.md); for voices without timestamps (Fish Audio, OpenAI, recordings) also
`pip install faster-whisper`, so word timings are measured from the audio instead of estimated.

## Workflow

### 1. Brief: ask before you build
Before planning anything, ask the client these six, even when the request seems clear. Each changes what you
build, some cost money, and none can be inferred safely. Use AskUserQuestion when available: two rounds at
most (it takes four questions per round), with "Other" for paths and descriptions. Ask for files by path.
1. **Brand documentation**: a brand guide, colours, fonts, rules? Without one, the default Apple look.
   With one, read it and turn it into a theme.js (references/engine-api.md, Theme) before planning.
2. **Logos**: files to show (path, SVG preferred), and where: the corner, the intro, the end card. None is a
   fine answer.
3. **Voice**: none (unnarrated), a free voice (local Windows SAPI, macOS `say`, Piper: synthetic, good for
   drafts), or a paid service and which voice (ElevenLabs, Fish Audio, OpenAI, Azure, Polly...), or a
   recording of their own. Never choose a paid service for them: it spends their credits. Keys stay in the
   environment.
4. **Music**: a generated score (a calm pad with small accents on the beats; say the mood: bright, calm,
   serious), a music file of their own as the background (path; check its licence), or none.
5. **Captions** (narrated films): yes (an .srt plus a switchable subtitle track, default) or no.
6. **Intro and outro**: none, or for each one either a **description** (what it says and shows: e.g. "the
   logo, then: Acme presents: <title>") that you build as a short scene, or a **video** they supply (path).

Then settle, asking only what you cannot infer: topic and the one idea to leave with; audience; target length
(20-40 s unnarrated, 45-90 s narrated is typical, plus the intro and outro); where the facts and data come
from. Use synthetic or properly sourced data; never real people's records. Record every answer in plan.md.

### 2. Plan (before code)
Read references/design.md. Write `<film>/plan.md` with: the brief answers, thesis, signature moment, colour
roles (one meaning each, with text contrast), type scale, layout sketch, 4-6 beats with their on-screen
words, and a critique pass ("would this plan fit any topic? then it is a template"). For a narrated film,
write the script into narration.json now (references/narration.md section 1): on-screen titles must be words
the voice says. Write the intro and outro sentences too when they are built from a description.

### 3. Scaffold
```
python <skill>/scripts/new_film.py <project> <film-name> [--narrated] [--title "..."] [--theme theme.js] [--assets logos/]
    [--intro-text "..." [--intro-title "..."] | --intro-video FILE] [--outro-text "..." [--outro-title "..."] | --outro-video FILE]
cd <project> && npm i puppeteer-core      # once per project
```
This copies the engine to `<project>/engine/` (once; `--update-engine` refreshes an older copy) and a
working starter film (index.html, film.js, score.js, narration.json or beats.js) to `<project>/<film-name>/`.
A theme.js sets `window.THEME`, with the logo in `THEME.logo` (see references/engine-api.md); copy the default
block from engine/motion.js to start one. The bookend options are in "Intro, outro and music" below.

### 4. Narration (optional)
Generate the voice the client chose, first, so the picture can be timed to it (references/narration.md):
- ElevenLabs: `ELEVENLABS_API_KEY=... python engine/make_film.py <film> --voice elevenlabs [--voice-id ID]`.
- Fish Audio (MCP connector `fish-audio`), OpenAI, Azure, Polly, a free voice or a recording: one file per
  line as `<line id>.mp3` in a folder, then `python engine/make_film.py <film> --voice import:<folder>`.
- Free local voice on Windows: `--voice sapi`.
Every animation hangs on a word, so word timings must come from the audio. ElevenLabs, Azure, Polly and SAPI
return them; for any other voice make_film.py runs `align_whisper.py`, which measures them with local
speech-to-text (faster-whisper) and keeps the script's spelling. Check its report: each line should match at
least 80% of its words. Keep each voice in `vo-<id>/` (`--voice-id`) so rebuilding spends no credits.

### 5. Animate
Edit `<film>/film.js`, keeping the starter's structure: a timing object `T` built from `cue()`/`spoken()`
(narration) or `beat()` (beats.js); layout constants; one draw function per element, each a pure function
of t; `drawScene(t)`; `defineFilm`. Use the engine's components (card, pill, buildText, swapText, check,
padlock, strokeBez) before inventing new ones. Keep moves rigid and lifted, titles built from spoken words,
and every scene's end state readable as a still. Engine reference: references/engine-api.md. To find or
change engine code, read references/code-map.md first (every service and script function with line numbers).
Draw each card inside the same fade as its content: `card()` multiplies its alpha into `ctx.globalAlpha`, so
a helper that sets `ctx.globalAlpha = x` instead of `*= x` makes the card pop in empty before its text. Write
`*=` in every helper you add.

### Intro, outro and music
- **Intro or outro from a description**: `--intro-text "<sentence>"` (spoken in a narrated film, shown in a
  silent one) and optionally `--intro-title "<title>"` (large, accent colour; end the sentence with it to
  have it spoken). new_film.py makes `<film>/intro/` from assets/template/bookend: the theme's logo large,
  the sentence word by word, the title, a soft pad. It is a starting point: restyle scene.js to the
  description (keep one logo per frame). Same for `--outro-*` in `<film>/outro/`. For an imported voice,
  put `intro.mp3` / `outro.mp3` beside the film's line files.
- **Intro or outro as a video**: `--intro-video FILE` / `--outro-video FILE` copies the clip to
  `<film>/bookends/`. It is joined as it is: scaled and padded to 1080p (never stretched), 60 fps, its sound
  levelled to the film's loudness.
- make_film.py builds the bookend scenes with the film's voice, then joins intro + film + outro
  (bookends.py) with one caption track. `--bookends none` delivers the film alone.
- **Music**: the generated score is score.js (chord, accents on the beats, ducked under the voice): set its
  chord for the mood the client asked for (major and open for bright or calm, no minor pad unless asked).
  For the client's file: `make_film.py <film> --music <file>`. The file becomes the bed (trimmed, faded,
  looped if short), 15 LU under the voice (`--music-level`, default -34 LUFS) and ducked 8 dB more under
  speech, with the score's accents kept on top. No music: delete the pad and accents from score.js.

### 6. Review (at least two passes; do not skip)
Render stills and look at them:
```
node engine/render.js stills <film>/index.html <film>/stills <times...>
python engine/sheet.py <film>/stills <prefix> <times...>            # 2x2 sheets for close looks
python engine/review.py <film>/stills <prefix> --palette-from <film>/theme.js   # contact sheet + palette
python engine/contrast.py <film>/theme.js
```
Pick times at every beat's start, its midpoint, just after each word that triggers a change, mid-move
(transitions are where overlaps hide) and the end card; for the contact sheet, one still per second. For
every card, take a still just before its content appears: the card must not already be there, empty. Take
2-3 stills of a built intro or outro too (`<film>/intro/index.html`). Check: overlaps and collisions, text
cut by cards, words appearing on their spoken time, reading time, colour meanings, contrast, the brand
(colours, fonts, logo untouched and unobstructed), the signature moment. Fix, re-render the affected times,
repeat. Record what you found and fixed in plan.md under Review notes.

### 7. Score, mix, render
```
python engine/make_film.py <film> --voice keep [--music FILE] [--captions none]   # or --voice none
```
make_film.py is an orchestrator: it runs the services in `engine/services.json` (voice, align, timeline,
score, music file, mix, render, captions, intro, outro, bookends, check). Each service is one script that
talks to the others only through files in the film folder, and is skipped when its outputs are newer than
its inputs and its command is unchanged; anything downstream of a changed file reruns. Flags: `--dry-run`
(what would run and why), `--only render`, `--from mix`, `--force [SERVICE]`, `--list`. Intermediate files
go in `<film>/build/`.
Output: `<film>/<film-name>.mp4`, 1920x1080, 60 fps, mix at -16 LUFS / -1.5 dBTP (`--lufs` to change), with
`<film-name>.srt` next to it and a subtitle track when there are captions. make_film.py ends with
`check_film.py`: one PASS/WARN/FAIL line each for video, audio, timings, captions, bookends, tail, alpha. Fix
every FAIL before delivery. It checks files, not looks: still pull 2-3 frames from the MP4 and look at them.

### 8. Report
File path, length (intro + film + outro), loudness, the voice used and how word timings were obtained
(native, measured with the share of words matched, or estimated, and why), the music (generated, or the
client's file and its licence), the captions file, the check_film.py output (quoted), what you reviewed and
fixed, and what you did not check (for example, you cannot listen to the audio: say so). Offer the next
useful step (another voice, another music file, a 9:16 cut).

## Reference files
- references/design.md: design principles, colour, type scale, layout, motion rules, craft lens, past mistakes.
  Read before planning.
- references/narration.md: script format, voice services, word timings (native, measured, estimated),
  captions, keys and credits, using cues in the film.
- references/engine-api.md: every motion.js function, the theme, and the command lines.
- references/code-map.md: the services (what each reads, writes and needs), the pipelines, and every
  script's functions with line numbers, generated from a graphify graph (references/code-graph/graph.json).
  Maintainers: after changing scripts/ or assets/, run tools/build_code_graph.py.

## Scripts
`new_film.py` scaffold · `make_film.py` orchestrator (services.json) · `render.js` stills/video · `motion.js`
design engine · `tts_elevenlabs.js`, `tts_sapi.ps1`, `import_voice.py`, `align_whisper.py`,
`align_estimate.py` narration · `build_timeline.js` cues + voice track · `audio-lib.js` synth ·
`music_file.py` supplied bed · `mix.js` loudness · `make_captions.js`, `attach_captions.py` captions ·
`bookends.py` intro + film + outro · `check_film.py` delivery checks · `review.py`, `sheet.py`,
`contrast.py` review aids.
