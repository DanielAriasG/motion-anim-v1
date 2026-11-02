# Prompt template

This template is a fill-in brief for one film. It follows the structure of the prompt behind "Anonymization and
pseudonymization of structured data" (Film 1, v9), the narrated pilot this skill was built from. A worked
example of that film follows the template.

**How to use it**
1. Copy the block below and fill in the `<...>` placeholders.
2. Delete the lines that don't apply.
3. Paste it into Claude with the skill installed.

The six **BRIEF ANSWERS** are the questions the skill asks before it builds. If they are answered here, it
doesn't need to ask them.

```
FILM · <TITLE> (<narrated | silent>, <target length, e.g. 60-90 s>)

IDEA
What the film explains: <one sentence>.
Headline (the line people remember): "<headline>"
Audience: <who>. Feeling: <e.g. precise, calm, trustworthy, with one moment of surprise>.
Core message: <2-3 sentences: what the viewer must understand by the end>.

BRIEF ANSWERS (the six questions the skill asks)
1. Brand documentation: <path to brand guide, or "none: default Apple look">
   Colours (hex), fonts, rules to respect: <...>
2. Logos: <path(s), SVG preferred>, placed <corner top-left | top-right | intro | end card | none>
3. Voice: <none | free local voice | ElevenLabs (API key / MCP) | Fish Audio (MCP / API key) | other | my recording>
   Voice name or ID: <...>. Language: <en | es | ...>. Clips already made: <folder or "no">
4. Music: <generated: mood <bright | calm | serious> | my file <path> (licence: <...>) | none>
5. Captions: <yes: .srt + subtitle track | no>
6. Intro: <none | description: "<what it says and shows>" | video: <path>>
   Outro: <none | description: "<...>" | video: <path>>

NARRATION (if narrated)
One line per beat; on-screen titles are the spoken words, built word by word as they are said.
Write for the ear: short sentences, no abbreviations the voice would misread. ~130-150 words per minute.
<paste the script, or "write it from the beats below">

GRAPHICS
- Content in white cards on a light canvas; familiar components: <tables, pills, cards, charts...>
- Type: the system face (or the brand fonts); hierarchy by size and weight.
- Motion: calm springs, one thing at a time; nothing passes through readable text.
- One signature moment: <the single frame people will remember>
- Header / chapter label: <text, or none>

COLOUR (one colour, one meaning)
<colour #hex> means <...> · <colour #hex> means <...> · <colour #hex> means <...>
Text is black or white on fills (check contrast).

DATA RULE
<e.g. every record is synthetic: invented names, IDs and places. Never real people or real rows.>
Sources for facts and figures: <...>

STORY BEATS (each one narrated)
1. Hook: <...>
2. <...>
3. Peak / signature moment: <...>
4. <...>
5. End card: the headline, <series title>, source line: "<sources>", <logos / funding text>.

REFERENCES ON SCREEN (optional)
<law articles, papers, guidance: short chips on the beats they support, full citation on the end card>

DELIVERY
<output path/name>.mp4, 1920x1080, 60 fps, -16 LUFS (or <-16.9 to match a series>), captions as above.
Review stills at every beat before the final render; report what could not be checked.
```

---

## Worked example: Film 1 v9 (filled template)

This is the latest Film 1 brief, rewritten into the template. It uses the eCAN Plus brand. For eCAN Plus
films use the eCAN Motion Anim skill, where the brand, intro and outro are built in. Any other client fills
the same fields with their own brand.

```
FILM · ANONYMIZATION AND PSEUDONYMIZATION OF STRUCTURED DATA (narrated, ~85 s + intro + outro)

IDEA
What the film explains: how anonymization and pseudonymization work on a table of health records.
Headline: "A name is not the only thing that names you."
Audience: hospital data stewards, researchers and DPOs. Feeling: precise, calm, trustworthy,
with one moment of unease.
Core message: removing the name is pseudonymization, and the data is still personal while a key
exists. Re-identification happens through combinations (postcode + date of birth + sex).
Generalization breaks those combinations.

BRIEF ANSWERS
1. Brand documentation: eCAN Plus Brand Identity Guideline. Colours: green #026873, coral #ED6D7C,
   turquoise #41B9C6, light coral #F1A6A0, grey #C1D0D9 (tints and shades only, no new hues).
   EU emblem and funding statement mandatory.
2. Logos: eCAN Plus short logo top-right, 80 px high (SVG, exact size); EU "Co-funded by" lockup
   on the end card and the intro.
3. Voice: Fish Audio through the MCP connector, voice "Ethan" 536d3a5e000945adb7038665781a4aca,
   model s2.1-pro, English. One call per line; clips kept in fish-ethan/. Word timings measured
   from the audio (faster-whisper).
4. Music: my file Free-audios/musinova-calm-ambient-science-medical-tech.mp3, low under the voice;
   keep the generated sound effects on the beats. (Second version: a generated bed, major chords,
   bright, not gloomy.)
5. Captions: yes (.srt + subtitle track).
6. Intro: description: the big horizontal eCAN Plus logo, the EU block, and the spoken sentence
   "eCAN Plus, a European Joint Action bringing the benefits of digital health to cancer centres,
   presents: anonymization and pseudonymization of structured data."
   Outro: video: eCANPlus_outro.mp4.

GRAPHICS
- White cards (radius 28, soft shadow) on a light canvas tinted from the brand grey. Familiar
  components: tables, capsule pills, a key card, a contact card.
- Type: Segoe UI Variable Display and Text; Consolas for codes and tokens. Pills and chips bold.
- Signature moment: the re-identified row becomes a contact card (coral monogram, name,
  "Re-identified", the diagnosis attached).
- Header: "Anonymization and pseudonymization of structured data", top-left, green; the technique
  the voice is on lights up in a green capsule.

COLOUR
coral = identifies a person · turquoise = hints at a person (quasi-identifiers) · green = protected
or safe (tokens, generalized values, passed tests) · green-900 = the key · light coral = outside data
(the register) · grey = sensitive attribute.

DATA RULE
Every record is synthetic. Generalization follows EDPB Guidelines 02/2026 (draft), Examples 10 and
12: dates of birth become 1946, postcodes 54***.

STORY BEATS
1. Hook: "You don't need a name to find someone." becomes the title; the patient table appears,
   each column's role named as it is spoken.
2. Pseudonymization: name and ID lift out into a dark key card, tokens replace them, the key locks
   ("held separately"). "Pseudonymized data is still personal data."
3. Peak: a public register; sex, date of birth and postcode match as they are said; the token
   becomes a person (the contact card). "No name needed."
4. Anonymization: generalize, regroup into two k = 3 groups; the EDPB's three tests answered "No".
4b. What stays: the diagnosis stays; "Health data may serve research, with safeguards."
5. End card: the headline, series title, source line, EU block; authorship card.

REFERENCES ON SCREEN
Chips: "Art. 4(5)" beside the key, "Recital 26" beside the title, "Art. 5(1)(c) minimisation"
beside "Generalized", "Art. 9 · special category" on the diagnosis. End card: "GDPR Arts. 4(5),
5(1)(c), 9(2)(j), 89(1); Recital 26. Not legal advice."

DELIVERY
renders/privacy-01-structured-v9-ambient.mp4 and -generated.mp4: 1920x1080, 60 fps,
-16.9 LUFS, captions .srt + subtitle track.
```
