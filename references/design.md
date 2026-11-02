# Design guide for motion films

Distilled from Apple's Human Interface Guidelines (via github.com/dickwu/apple-design-skill: design
principles, color, typography, layout, motion, materials, branding, accessibility) and from building
narrated explainer films with this engine. Apple writes for apps; the principles carry over to a 1920x1080
film once you translate "control" into "on-screen element" and "interaction" into "a beat of the story".

## Contents
1. Principles as questions
2. Plan before drawing (the token plan)
3. Colour
4. Type
5. Layout
6. Motion
7. Craft lens
8. Accessibility floor
9. Mistakes we already made (so you don't)

## 1. Principles as questions

| Principle | Question for a film |
|---|---|
| Purpose | What is the one idea a viewer must leave with? Does every scene serve it? |
| Familiarity | Are we showing things people already know (a table, a card, a contact, a checklist) rather than inventing UI? |
| Simplicity | Has every element earned its place? Can one be removed? |
| Craft | Spacing, alignment, wording, timing: is every frame finished? |
| Delight | Is there one moment with feeling, and is it the right feeling? Delight is not decoration. |
| Responsibility | Is the data synthetic and the claim sourced? |

## 2. Plan before drawing

Write this in the film's plan.md before any code. It is the cheapest place to make the film good.

- **Thesis**: one sentence: what the film is for and what it will be remembered by.
- **Signature**: the single defining moment (e.g. a table row that turns into a contact card). Spend the
  boldness there; keep everything around it quiet.
- **Colour roles**: 4-8 named colours, each with ONE meaning, with the contrast of the text that sits on it.
- **Type scale**: display, title, body, data, caption sizes (below).
- **Layout**: one sentence plus a rough sketch of the main frame (where the title, the content card and the
  side panel live).
- **Beats**: the story in 4-6 beats, each with its on-screen words.
- **Critique**: would this plan fit a different topic unchanged? Then it is a template. Revise it until the
  visuals come from the subject's own materials (records, documents, forms, scans, waveforms...).

## 3. Colour

- **One colour, one meaning** (HIG color › "Avoid using the same color to mean different things"). Decide the
  meanings first: e.g. red = identifies a person, teal = a hint, green = safe/protected, grey = neutral.
  Then a viewer reads the colour before the words.
- **Vary with tints and shades, not new hues.** A palette of 4-6 base colours plus their tints (backgrounds
  of columns, chips) and one deep shade (a dark card for a "locked" or "secret" object) gives variety without
  breaking a brand. Derive them in the theme (`derive: { blue50: ['tint', 'blue', .9] }`).
- **Text on fills is white or black.** Pick by contrast (`python engine/contrast.py theme.js`). A pair at
  about 3:1 (white on Apple blue, white on a mid coral) is acceptable only for bold or large text: make those
  pills and chips bold.
- **Colour is never the only carrier.** Every coloured group also has a label (a pill, a legend line).
- **Background**: a light grouped canvas (Apple gray6 #F2F2F7, or a 20 % tint of a brand grey) with white
  cards on it reads cleaner on video than pure white, and lets cards separate by shadow instead of borders.
  No grain or noise textures: they read as compression noise on screen.

Default Apple palette (light, in motion.js): blue #007AFF, green #34C759, red #FF3B30, orange #FF9500,
yellow #FFCC00, teal #30B0C7, indigo #5856D6, purple #AF52DE, pink #FF2D55, greys #8E8E93 to #F2F2F7,
secondary text #6E6E73, link #0066CC. Apple notes system values can shift between releases; for a film they
are a fixed starting point.

## 4. Type

- Use the platform's system face: SF Pro (macOS), Segoe UI Variable (Windows 11), else Inter. motion.js picks
  the first installed. Display optical size for titles, Text for everything else; one mono for codes and IDs.
- Hierarchy by size and weight, never by a second display font. Avoid light/thin weights.
- Scale for 1080p video (viewed at 50 % on a phone, so the minimum matters):

| Role | Size | Weight |
|---|---|---|
| Hook / end headline | 88-104 px | 700 |
| Scene title | 56 px | 700 |
| Card heading | 28-32 px | 600 |
| Body, list items | 23-28 px | 400-600 |
| Table data | 20-22 px | 400 (mono for IDs) |
| Labels, pills | 17-20 px | 600-700 |
| Legal / funding text | 19 px minimum | 400 |

- On-screen words should be the spoken words (or a literal subset). When the narration says it, the
  matching word appears; this is what makes a narrated film feel precise.

## 5. Layout

- Margin 120 px. Title top-left at baseline ~196. Content in cards: a main card (~1100 px wide) and a side
  panel (~520 px) whose content changes per scene (legend -> key -> register -> tests) is a strong default
  for explainers: the main object stays put while the context changes beside it.
- Order by importance: top to bottom, leading to trailing. Align to scan; indent for hierarchy; group with
  space or a card, not lines.
- Logos defer to content: one small logo in a fixed corner, never repeated, never in the content area.
- Progressive disclosure: introduce one column group, one panel, one idea at a time.

## 6. Motion

- **Purposeful, brief, precise.** Motion explains a change (a value replaced, an item moved into a key, rows
  regrouped). If it explains nothing, cut it.
- **Springs, no bounce**: `P(t, start, dur)` uses a critically damped spring; `easeIO` for exits.
  Entrances 0.5-0.8 s, state changes 0.4-0.6 s, moves 0.9-1.1 s.
- **Words build as they are said**: `buildText` fades each word up out of a short blur at its spoken time.
- **One thing at a time.** Stagger by 60-80 ms only for small siblings (rows landing); never stagger items
  that travel far, move them as one rigid block.
- **Nothing passes through readable text.** A moving element lifts (shadow up, on its own white or tinted
  card) and travels above; rows that reorder are drawn last as lifted cards. Word-by-word magic moves
  (a hook that shrinks into a title) settle line one before line two moves.
- **Reading time** (unnarrated text): from fully on screen to the next change, at least
  max(2.5 s, 1 s + 1 s per 3 words). With narration the voice sets the pace; add 0.5-1.5 s gaps between
  lines and 1.2-1.8 s before a new scene so the picture changes in silence.
- **End card** holds 4-6 s after the last word, longer if it carries legal or funding text.
- Motion is never the only carrier of meaning: the end state of every animation must explain itself as a still.

## 7. Craft lens (run it on the contact sheet)

- Does it have a point of view: what is the one frame people would remember?
- Is it a template? Watch for: big number over a small label with a gradient; 01/02/03 markers on things that
  are not a sequence; hairline-rule broadsheet layouts; cream background with a serif and a terracotta accent.
- Is the boldness spent in one place?
- Remove one accessory. If nothing can go, say so.
- Every label says what it is ("Held separately", "No unique match"), sentence case, no jargon.

## 8. Accessibility floor

- Contrast: 4.5:1 for normal text, 3:1 for bold/large. Compute it (contrast.py), do not eyeball it.
- Minimum 17 px for anything a viewer must read; 19 px for legal text.
- Colour is always doubled by a label or shape.
- No flashing; no fast full-screen motion; blur transitions stay short (<0.5 s).
- Narrated films: on-screen words match the speech, and unless the client declines, the full narration ships
  as captions (.srt plus a subtitle track in the MP4, built from measured word timings; references/narration.md
  section 4).

## 9. Mistakes we already made (so you don't)
- Cards that popped in empty: a helper set `ctx.globalAlpha = a` inside card(), overriding the fade it was
  drawn in. Every card appeared at full opacity when its scene began, and its text faded in up to 4 s later
  (an info card stood empty beside an X-ray). Helpers multiply alpha (`*=`); check_film.py flags any that
  set it; review a still just before each card's content appears.
- Word timings estimated for a voice without timestamps (Fish Audio) were off by up to 0.64 s, so a word lit
  up after it was said. Measure them from the audio (align_whisper.py) before animating to them.
- A card sized for its first content overflowed when the content changed: three six-line columns spilled out
  of a transcript card. Size a card for the largest state it will hold, and check the busiest frame.
- A citation drawn as a filled pill reads as a state. Citations and references are outlined; states are filled.
- A frame that shows a logo large (intro, credits) next to the corner logo shows two logos: fade the corner
  logo out there (`defineFilm({ logo: t => ... })`).
- Scaling a pulsing chip from its left edge pushes it into the text beside it; scale from its centre.
- A music bed at the usual score level fought the voice; a full music track sits about 15 LU under the voice
  and ducks a further 8 dB while it speaks (make_film.py --music does this).
- Paper grain / gaussian noise texture: looked like video noise. Plain canvas instead.
- Text held too briefly: viewers could not read it. Use the reading-time rule or let narration pace it.
- 12 small chips flying from a table to a key at once: busy and unreadable. One panel, one move.
- Rows reordering by sliding through each other: unreadable for half a second. Lift moving rows as cards.
- A hook gliding into a title where line two crossed line one. Settle lines in order.
- Two cards overlapping a subtitle and column headers. Check every hold frame, not just the beat starts.
- A colour used for three meanings (coral for identifiers, warning, and highlight). Assign meanings first.
- Downscaling a 3500 px logo in canvas: soft and aliased. Pre-size raster logos to their exact pixels
  (Lanczos) and draw SVG logos with width/height set to the drawn size.
