# Motion Anim V1

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

## Install
- **claude.ai**: upload `motion-anim-v1.skill` (a zip of this folder without `evals/`) under
  Customize → Skills.
- **Claude Code**: copy this folder to `~/.claude/skills/motion-anim-v1/`.

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

## Requirements
Node 18+, Python 3 with Pillow, ffmpeg/ffprobe on PATH, Chrome or Edge, `npm i puppeteer-core` in the
project folder. For voices without timestamps: `pip install faster-whisper`.

## Layout
- `SKILL.md`: the workflow.
- `references/`: design, narration, engine API, code map.
- `scripts/`: the engine and its services (`services.json`, run by `make_film.py`).
- `assets/template/`: the starter film and the intro/outro scene.
- `tools/build_code_graph.py`: rebuilds `references/code-map.md`.
- `evals/`: test cases. Not run yet: see `evals/PENDING.md`.

API keys are read from the environment only. Never commit one.
