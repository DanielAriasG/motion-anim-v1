# Narration (optional)

A narrated film is driven by the voice: every title, animation and music accent is tied to a spoken word,
so changing the voice or a line re-times the whole film. Without narration, timing comes from beats.js.

## Contents
1. Writing the script (narration.json)
2. Choosing a voice service
3. Getting word timings
4. Captions
5. Keys and credits
6. Using cues in the film
7. Known problems

## 1. Writing the script

```json
{
  "voice": { "elevenlabs_voice_id": "onwK4e9ZLuTAKqWW03F9", "model_id": "eleven_multilingual_v2", "sapi_draft": "Microsoft Zira Desktop" },
  "lines": [
    { "id": "s1a", "scene": "hook", "gap": 0.8, "text": "You don't need a name to find someone." },
    { "id": "s1b", "scene": "table", "gap": 1.0, "text": "Take a simple table of patients. ..." }
  ],
  "tail": 6.0
}
```

- One line per beat; 1-3 sentences each. `gap` = silence before the line (0.5-1 s inside a scene,
  1.2-1.8 s before a new scene). `tail` = time after the last line (end card; 6 s if there is legal text).
- Write for the ear: short sentences, concrete nouns, no parentheses or abbreviations the voice will misread
  ("for example", not "e.g."; spell numbers the way they should be said if unsure).
- The words you want on screen must appear verbatim in the line (titles are built from spoken words).
- Explain each main part of the film in the order it appears. ~130-150 words per minute.

## 2. Choosing a voice service

The brief asks the client which one (SKILL.md step 1): a paid service with its voice (ElevenLabs, Fish Audio,
OpenAI, Azure, Polly...), a free one (the local Windows voice, macOS `say`, Piper), a recording of their own,
or no narration at all. Never pick a paid service for them: it spends their credits.

| Service | Word timings | Notes |
|---|---|---|
| ElevenLabs (`tts_elevenlabs.js`) | yes, native (with-timestamps endpoint) | Best default. Free plan: premade voices only via API (e.g. Daniel `onwK4e9ZLuTAKqWW03F9`, George `JBFqnCBsd6RMkjVDRZzb`, Alice `Xb7hH8MSUJpSbSDYk0k2`, Lily `pFZP5JQG7iQjIQuC4Bku`, Brian `nPczCjzI2devNBz1zQrb`, Sarah `EXAVITQu4vr4xnSDxMaL`). Library voices need a paid plan. |
| Fish Audio (MCP connector or API) | no (measured by align_whisper.py) | Connector: `claude mcp add --transport http fish-audio https://api.fish.audio/mcp`, then `/mcp` to sign in. Its `text_to_speech` tool returns an audio link per call; download one file per line as `<id>.mp3` and run `import_voice.py`. |
| OpenAI TTS (gpt-4o-mini-tts, tts-1) | no (measured by align_whisper.py) | Good quality, steerable tone. |
| Azure Speech | yes (word boundary events) | Save boundaries as `<id>.words.json` next to the audio, then import. |
| Google Cloud TTS | partial (SSML marks / timepoints) | Mark each word if you need exact times, else import + estimate. |
| Amazon Polly | yes (speech marks, type word) | Save marks as `<id>.words.json`, then import. |
| Cartesia, Deepgram Aura, PlayHT | varies (check current docs) | Import; use their timestamps if offered. |
| Local Windows voice (`tts_sapi.ps1`) | yes | Free draft for timing checks only; robotic. |
| macOS `say` / Piper (offline) | no | `say -o line.aiff "..."`; import + estimate. |

Offer to generate the first line in 2-3 voices so they can choose by ear (it costs ~40 characters each).
Free voices are fine for drafts; say in the report that a free voice sounds synthetic.

## 3. Getting word timings (in order of precision)

The picture follows the words, so a timing error is a visual error: a highlight that lands half a second
after its word reads as a mistake. Use the best source the voice allows.

1. **Native timestamps**: ElevenLabs with-timestamps, Azure word boundaries, Polly speech marks, SAPI.
2. **Measured: speech-to-text with word timestamps** (`align_whisper.py`, the default for every other
   voice). faster-whisper transcribes each line locally (free, CPU, the script as its prompt). difflib
   aligns the recognised words to the script's words in order, and each script word takes the measured
   start and end. Words whisper writes differently (numbers as digits, merged hyphenations) are spread over
   the gap between their matched neighbours. The script's spelling is kept.
   - make_film.py runs it after the import.
   - It skips lines with native or given timings, keeps the estimate as `vo-estimated/<id>.json`, and keeps
     the estimate for a line where under half the words match.
   - Read its report: 80-100% matched per line is normal. Low matches mean the voice said something else.
     Listen to that line, then fix the script or regenerate the line.
   - Non-English films: set `"language": "es"` (etc.) in narration.json; it then uses the multilingual model.
   - Install: `pip install faster-whisper`. The model downloads once (~460 MB for small).
   - Other speech-to-text services with word timestamps (Deepgram, AssemblyAI, ElevenLabs Scribe) work the
     same way: save `[{w, s, e}]` as `<id>.words.json` beside the audio before importing. Fish Audio's
     `speech_to_text` returns plain text only: use it to check the words, not the timing.
3. **Forced alignment** of known text to audio: ElevenLabs `/v1/forced-alignment` (needs that permission on
   the key), WhisperX, or Montreal Forced Aligner, if already set up.
4. **Estimate** (`align_estimate.py`, no dependencies): ffmpeg finds the pauses, and the words are spread
   over the speech between them. Use it only as a draft, or when faster-whisper cannot be installed. Against
   ElevenLabs timestamps: median error 0.06 s, 90% within 0.17 s, worst 0.72 s. Against measured timings on
   a Fish Audio series: mostly 0.1-0.3 s off, worst 0.64 s. Say so in the report when a film ships with
   estimated timings.

All paths end in the same files: `vo/<id>.wav` (48 kHz mono) and `vo/<id>.json` =
`{ engine, timing: native|given|estimated|measured, dur, words: [{ w, s, e }] }`. Then `build_timeline.js`
writes `cues.js` and `vo-track.wav`. Measuring changes word times inside each line, not line lengths, so a
film that is already built only needs build_timeline.js, the score and the mix run again before rendering.

## 4. Captions

The brief asks whether the client wants captions (default yes for a narrated film: films are often watched
muted and by non-native speakers, and the on-screen titles carry the key ideas, not the whole argument).
With captions off, run make_film.py with `--captions none`.
- `make_captions.js <film> <out.srt>` builds them from cues.js:
  - one sentence per caption, at most two lines of 42 characters;
  - a sentence that would fill both lines splits at a clause break;
  - lines prefer clause breaks and never end on "the", "a", "of" and similar;
  - each caption shows from its first word to 0.35 s after its last;
  - a line may choose its own breaks with `"captions": ["chunk", "chunk", ...]` in narration.json (each
    chunk one caption, still wrapped), e.g. so a name never stands alone on a caption.
- Captions are only as good as the timings: measure them first (section 3).
- make_film.py writes `<film>.srt` next to the MP4 and muxes it in as a switchable subtitle track (mov_text,
  language from narration.json). `--captions none` turns this off.
- Not burned in by default: viewers can switch them off and nothing in the frame is covered. If a platform
  needs open captions (some social feeds), burn a copy separately, set high enough to clear anything at the
  bottom of the frame (for example
  `ffmpeg -i film.mp4 -vf "subtitles=film.srt:force_style='MarginV=120,FontSize=22'" film-open.mp4`), and
  check the end card frames.
- With bookends, the delivered .srt holds the intro's captions, the film's shifted by the intro's length, and
  the outro's after them; the film's own .srt stays in `<film>/build/`. A supplied intro or outro clip brings
  no captions of its own.
- Read the .srt once: a caption is a quotation of the narration, so it must match the voice word for word.

## 5. Keys and credits

- Pass keys as environment variables at run time (`ELEVENLABS_API_KEY=... python engine/make_film.py ...`).
  Never write a key into the project, a script or a memory file. If a user pastes a key in chat, suggest
  rotating it afterwards.
- ElevenLabs keys can be restricted: 401 `missing_permissions` names the permission to enable
  (text_to_speech, forced_alignment, voices_read, user_read).
- A full 90 s narration is ~1,000 characters. Keep each voice's files (`--voice-id` stores them in
  `vo-<id>/`) so re-renders do not spend credits again.

## 6. Using cues in the film

```js
const T = {
  table: cue('s1b', 'take'),            // start of the first spoken "take" in line s1b
  sens: cue('s1b', 'diagnosis'),
  out: lineStart('s5') - 1.0,           // scene leaves 1 s before the end line
};
const TITLE = spoken('Pseudonymized data is still personal data.', 's2b');   // [{w, t}] per word
buildText([TITLE], M, 196, FD(56, 700), 56, 0, t, { out: lineStart('s3a') });
const SUB = spoken('the sensitive part.', 's1b', T.sens);   // `after`: skip an earlier "the"
```

cue() and spoken() throw if a word is missing, so a script edit that breaks a beat fails loudly at render.

## 7. Known problems

- Windows SAPI reports word positions scaled by sample rate / 16 kHz; tts_sapi.ps1 writes at 16 kHz to keep
  them exact.
- ElevenLabs 402 `paid_plan_required`: the voice is a library voice; pick a premade one or upgrade.
- A voice reads "ID" as "id" or a code letter by letter: rewrite the line, or spell it out.
- Repeated words: pass `after` to spoken(), or `n` to cue('id', 'the', 2).
- faster-whisper fails with `open() got an unexpected keyword argument 'metadata_errors'`: the installed PyAV
  is newer than it expects. align_whisper.py decodes the audio with ffmpeg itself, so this does not affect
  it; other scripts can do the same (16 kHz mono float32 into `model.transcribe`).
- On Windows, the Hugging Face model cache warns about symlinks; harmless.
