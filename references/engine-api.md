# Engine API (motion.js)

All functions are globals in the page. Everything is a pure function of `t` (seconds).

## Theme (window.THEME, set in theme.js before motion.js)
`colors {name: '#hex'}`, `derive {name: ['tint'|'shade', base, amount]}`, `roles {canvas, surface, ink,
secondary, hair, shadow}`, `on {fill: 'white'|'black'}`, `fonts {display: [...], text: [...], mono: [...]}`,
`logo {src, w, h, x, y}`, `margin`, `requireFonts`. Unset keys fall back to the Apple default.
`col(name, alpha)`, `ON[fill]` (text colour for a fill), `contrast(a, b)`, `FONTS_USED`.

## Type
`FD(size, weight=600)` display, `FT(size, weight=400)` text, `FM(size, weight=400)` mono -> CSS font strings.
`text(str, x, y, font, color='ink', alpha=1, letterSpacing=0, align='left')`, `measure(str, font, ls)`,
`wrapLines(str, font, maxWidth)`.

## Timing
`P(t, start, dur, ease=spring)` 0..1 progress; `vis(t, inAt, outAt, din=.5, dout=.4)` visibility;
`spring`, `easeIO`, `clamp`, `lerp`.
Narration: `cue(id, word, n=1)`, `lineStart(id)`, `lineEnd(id)`, `spoken(str, id, after)` -> [{w, t}].
No narration: `beat(name)` from window.BEATS; `readTime(str)`; `TOTAL` (from cues or window.DURATION).
`at(str, t0, color)` -> words all at t0 (for unspoken text).

## Text
`buildText(lines, x, y, font, size, lineHeight, t, {color, out, align, ls})` word-by-word build
(lines = [[{w, t, c?}]]). `swapText(a, b, x, y, fontA, fontB, colA, colB, p)` value replaced in place.

## Surfaces and marks
`card(x, y, w, h, {r=28, fill='surface', a, lift=1})` rounded card with soft shadow (lift >1 = raised).
`rrect(x, y, w, h, r, fill, a)`, `ring(x, y, w, h, r, color, lineWidth, a)`,
`pill(str, x, y, font, size, fill, p, {padX, h, align})` capsule centred on y,
`dot(x, y, r, color, a)`, `check(x, y, r, fill, p)`, `padlock(x, y, size, color, closed01, a)`,
`bez(p0, p1, p2, p3, u)`, `strokeBez(pts, u0, u1, color, width, a)`.

## Frame
`defineFilm({ scene(t), preload: [promises] })`. The shell paints the canvas colour, calls scene(t), then
draws the theme logo. `window.renderFrame(t)` and `window.ready` are what render.js uses.

## Command line (from the project folder)
- `python engine/new_film.py <project> <name> [--narrated] [--title "..."] [--theme theme.js] [--assets dir]
  [--intro-text "..." [--intro-title "..."] | --intro-video FILE] [--outro-text "..." [--outro-title "..."] | --outro-video FILE] [--update-engine]`
- `python engine/make_film.py <film> --voice elevenlabs|sapi|import:<dir>|keep|none [--voice-id ID] [--lufs -16]
  [--align auto|none] [--captions soft|none] [--music FILE] [--music-level -34] [--bookends auto|none]
  [--list] [--dry-run] [--only SERVICE ...] [--from SERVICE] [--force [SERVICE]]`
  (runs the services in engine/services.json and skips the up-to-date ones; references/code-map.md lists them)
- `python engine/align_whisper.py <film> [--force] [--model small.en]` (measure word timings; then build_timeline.js)
- `node engine/make_captions.js <film> <out.srt>` (captions from cues.js; narration.json `captions` chunks honoured)
- `python engine/attach_captions.py <video.mp4> <captions.srt> <out.mp4> [narration.json]` (subtitle track, not burned in)
- `python engine/music_file.py <film> <music file> [bed.wav]` (a supplied bed, trimmed and faded to the film)
- `python engine/bookends.py <film> <film video.mp4> <captions.srt|-> <out.mp4> [--lufs -16]` (intro + film + outro)
- `python engine/check_film.py <film> [<film.mp4>] [--lufs -16]` (delivery checks; exit 1 on any FAIL)
- `node engine/render.js stills <film>/index.html <film>/stills 2 5.5 9`
- `python engine/review.py <film>/stills <prefix> --palette-from <film>/theme.js [--ignore-after T]`
- `python engine/sheet.py <film>/stills <prefix> 2 5.5 9 12` (2x2 sheets for close review)
- `python engine/contrast.py <film>/theme.js`
