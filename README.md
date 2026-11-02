# Motion Anim V1

**English** · [Español](README.es.md)

A Claude skill that makes motion-graphics videos: explainers, animated diagrams and narrated films. Each
frame is drawn in code on a canvas and rendered to a 1080p60 MP4. The design follows Apple's Human Interface
Guidelines.

Before building, the skill asks for six things:
1. brand documentation;
2. logos;
3. the voice: none, a free local voice, or a paid service such as ElevenLabs or Fish Audio;
4. music: generated, a file of your own, or none;
5. captions;
6. an intro and an outro, each from a description or a video you supply.

Once the six answers are in, it:
- times every animation to the narration's words, using word timings measured from the audio;
- delivers an .srt and a subtitle track;
- joins the intro, film and outro into a single file;
- mixes the audio to -16 LUFS;
- checks the result before delivery.

## Contents
- [Install the skill](#install-the-skill)
- [Install the requirements](#install-the-requirements)
- [Quick start](#quick-start)
- [Prompt template](#prompt-template)
- [Voices: Fish Audio and ElevenLabs (MCP or API key)](#voices-fish-audio-and-elevenlabs-mcp-or-api-key)
- [Branding](#branding)
- [Music](#music)
- [Intro and outro](#intro-and-outro)
- [Folder layout](#folder-layout)

## Install the skill
- **claude.ai**: upload `motion-anim-v1.skill` under Settings → Capabilities → Skills. The `.skill` file is a
  zip of this folder without `evals/`.
- **Claude Code**: copy this folder to `~/.claude/skills/motion-anim-v1/`.

## Install the requirements
The engine is JavaScript (Node.js) plus a few Python scripts. Chrome renders the frames, and ffmpeg encodes
the video and mixes the sound. The engine doesn't use React or any other front-end framework: each film is a
plain HTML page with a canvas.

| What | Why | Install |
|---|---|---|
| **Node.js 18+** (includes npm) | Runs the engine, the renderer and the score | https://nodejs.org (LTS), or `winget install OpenJS.NodeJS.LTS` |
| **puppeteer-core** | Drives Chrome to draw each frame | `npm i puppeteer-core` in your project folder, once |
| **Chrome or Edge** | The browser that renders the frames | Usually installed already |
| **Python 3.10+** with Pillow | Scaffold, orchestrator, review and checks | https://python.org, then `pip install pillow` |
| **ffmpeg / ffprobe** on PATH | Encoding, loudness, joining clips | `winget install Gyan.FFmpeg`, `brew install ffmpeg`, or `apt install ffmpeg` |
| **faster-whisper** (optional) | Measures word timings for voices that don't return them (Fish Audio, OpenAI, recordings) | `pip install faster-whisper` (the first run downloads a model of about 460 MB) |

To check the setup:
```
node --version && npm --version && python --version && ffmpeg -version
```

## Quick start
Ask Claude for a video, for example *"Make a 60-second narrated explainer on how vaccines work"*. The skill
asks its six questions, then scaffolds, animates, reviews and builds the film. The steps by hand:
```
python scripts/new_film.py <project> my-film --narrated --title "How vaccines work" \
    --intro-text "Science Basics presents: how vaccines work." --outro-video outro.mp4
cd <project> && npm i puppeteer-core
python engine/make_film.py my-film --voice sapi --music bed.mp3     # or --voice elevenlabs / import:<folder>
```
The result is `my-film/my-film.mp4` and `my-film.srt`, with the `check_film.py` report at the end of the run.

## Prompt template
[prompts/prompt-template.md](prompts/prompt-template.md) is a fill-in brief: the six brief answers, idea,
narration, graphics, colour, data rule, story beats and delivery. It follows the prompt behind Film 1
("Anonymization and pseudonymization of structured data", v9) and includes that film as a worked example.
Spanish version: [prompts/plantilla-prompt.md](prompts/plantilla-prompt.md).

## Voices: Fish Audio and ElevenLabs (MCP or API key)
Each service can be used in two ways:
- **MCP connector**: Claude calls the service as a tool in the conversation and saves the audio files. You
  sign in once; no key goes into a command.
- **API key**: a script calls the service directly. The key goes in an environment variable for that
  command only.

Keep keys out of files, scripts and chat. If you paste a key into a chat by mistake, rotate it.

### ElevenLabs
ElevenLabs returns word timings, so its timing is the most precise.
- **API key** (built in):
  ```
  # macOS / Linux / Git Bash
  ELEVENLABS_API_KEY=sk_... python engine/make_film.py my-film --voice elevenlabs --voice-id <voice id>
  # PowerShell
  $env:ELEVENLABS_API_KEY="sk_..."; python engine/make_film.py my-film --voice elevenlabs --voice-id <voice id>
  ```
  - Free plans can use the premade voices only, for example Daniel `onwK4e9ZLuTAKqWW03F9`.
  - The voice is saved in `vo-<voice id>/`, so rebuilding spends no credits.
- **MCP**: ElevenLabs publishes an MCP server (`elevenlabs-mcp`; see the ElevenLabs docs for the current
  install command, which also takes your key). Claude saves one file per narration line as `<line id>.mp3`
  in a folder. Then:
  ```
  python engine/make_film.py my-film --voice import:<folder>
  ```
  Files made this way carry no timings, so they are measured from the audio (needs faster-whisper).

### Fish Audio
Fish Audio returns no word timings. They are always measured from the audio, so install faster-whisper.
- **MCP** (recommended):
  ```
  claude mcp add --transport http fish-audio https://api.fish.audio/mcp
  ```
  - Then run `/mcp` in Claude Code to sign in.
  - Claude generates one file per line with your chosen voice and saves each as `<line id>.mp3`.
  - The intro and outro lines go in the same folder as `intro.mp3` and `outro.mp3`.
  - Then run `python engine/make_film.py my-film --voice import:<folder>`.
- **API key**: call the Fish Audio text-to-speech API (`POST https://api.fish.audio/v1/tts` with
  `Authorization: Bearer $FISH_API_KEY` and your voice's `reference_id`; see docs.fish.audio for the current
  model and parameters). Save one MP3 per narration line as `<line id>.mp3`, then import the folder the same
  way.

### Free and other voices
- `--voice sapi` uses the free Windows voice, which sounds synthetic. Good for timing drafts.
- macOS `say`, Piper, OpenAI, Azure, Polly or your own recording: save one file per line and use
  `--voice import:<folder>`.
- `--voice none` makes a film without narration. Its timing comes from `beats.js`.

## Branding
The default look is Apple's light palette and system fonts. To use your brand, give the skill your brand
guide and logos when it asks, and it writes a `theme.js`. You can also write one yourself and pass it with
`new_film.py --theme theme.js --assets <folder with logos>`:
```js
window.THEME = {
  colors: { brand: '#026873', accent: '#ED6D7C', grey: '#9E9E9E', white: '#FFFFFF', black: '#000000' },
  derive: { brand50: ['tint', 'brand', .9] },            // tints and shades of your colours
  roles:  { canvas: 'brand50', surface: 'white', ink: 'black', secondary: 'grey', hair: 'brand50', shadow: 'black' },
  on:     { brand: 'white', accent: 'white' },           // text colour on each fill
  fonts:  { display: ['Montserrat', 'Arial'], text: ['Montserrat', 'Arial'], mono: ['Consolas'] },
  logo:   { src: 'logos/logo.svg', w: 160, h: 48 },      // drawn at this exact size, top-left by default
  margin: 120,
};
```
- Give each colour one meaning.
- Check text contrast with `python engine/contrast.py theme.js`.
- Prefer an SVG logo, sized to how it is drawn.
- Only one logo shows per frame: the corner logo steps aside on an intro or credits card that shows it large.

## Music
Choose one when the skill asks:
- **Generated score** (default): `score.js` plays a soft pad plus small sound effects on the animation's
  beats. It is ducked under the voice. Tell the skill the mood (bright, calm, serious) and it sets the chords.
- **Your own music file**:
  ```
  python engine/make_film.py my-film --music path/to/music.mp3 [--music-level -34]
  ```
  - The file is trimmed to the film, faded in and out, and looped if it is too short.
  - It sits 15 LU under the voice and drops 8 dB more while anyone speaks.
  - The score's sound effects stay on top.
  - Check that the track's licence allows your use.
- **None**: remove the pad and the effects from `score.js`.

## Intro and outro
Each can be built from a description, supplied as a video, or left out:
```
# built from a description: a short scene with your logo, the sentence and a title
python scripts/new_film.py <project> my-film --narrated --title "..." \
    --intro-text "Acme presents: how backups work." --intro-title "How backups work" \
    --outro-text "Thanks for watching." --outro-title "acme.example/learn"

# supplied as videos
python scripts/new_film.py <project> my-film --narrated --intro-video intro.mp4 --outro-video outro.mp4
```
- **Built scenes** live in `my-film/intro/` and `my-film/outro/`.
  - In a narrated film they are spoken with the film's voice. In a silent film they hold for reading time.
  - Edit `scene.js` there to restyle them.
  - With an imported voice, add `intro.mp3` and `outro.mp3` to the voice folder.
- **Supplied videos** are scaled to 1080p without stretching, set to 60 fps and levelled to the film's
  loudness.
- **Joining**: `make_film.py` joins intro + film + outro into one MP4, with one caption track across all
  three. Use `--bookends none` to deliver the film alone.

## Folder layout
- `SKILL.md`: the workflow Claude follows.
- `prompts/`: the prompt template in English and Spanish, with a worked example.
- `references/`: design guide, narration, engine API, code map.
- `scripts/`: the engine and its services (`services.json`, run by `make_film.py`).
- `assets/template/`: the starter film and the intro/outro scene.
- `tools/build_code_graph.py`: rebuilds `references/code-map.md` after code changes.
- `evals/`: test cases. Not run yet: see `evals/PENDING.md`.
