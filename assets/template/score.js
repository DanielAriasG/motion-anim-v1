// Score for __TITLE__: a quiet pad, small accents on the visual beats, ducked under the voice.
//   node score.js music.wav            pad + accents
//   BED=none node score.js accents.wav  accents only (with a supplied music file)
// Timing comes from cues.js (narration) or beats.js, the same source the picture uses.
const fs = require('fs');
const path = require('path');
const here = f => path.join(__dirname, f);
const CUES = fs.existsSync(here('cues.js')) ? require('./cues') : null;
const B = !CUES && fs.existsSync(here('beats.js')) ? require('./beats') : { BEATS: {}, DURATION: 20 };
const TOTAL = CUES ? CUES.TOTAL : B.DURATION;
process.env.DUR = String(TOTAL);
const A = require('../engine/audio-lib');
const { ramp, SR, N, L, R } = A;

const norm = s => s.toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9'*-]/g, '');
function cue(id, word, n = 1) {
  for (const w of CUES.lines[id].words) if (norm(w.w) === word && --n === 0) return w.s;
  throw new Error(`cue: "${word}" not in ${id}`);
}
// the same beats as film.js
const T = CUES
  ? { title: CUES.lines.s1.t0, card: cue('s2', 'each'), items: [cue('s2', 'appears'), cue('s2', 'exactly'), cue('s2', 'said')], end: CUES.lines.end.t0 }
  : { title: B.BEATS.title, card: B.BEATS.card, items: B.BEATS.items, end: B.BEATS.end };

// ---------- pad: one calm chord (change the notes for the film's mood) ----------
const CHORD = [87.31, 130.81, 220.0, 261.63, 392.0];   // F major add9
const env = t => ramp(t, 0, 2.5) * (1 - ramp(t, TOTAL - 3, 2.8) * .9);
// BED=none: accents only (make_film.py --music FILE renders this as accents.wav and lays them over the file)
if (process.env.BED !== 'none') A.pad(CHORD.map(f => ({ f, w: () => 1 })), env, t => 1000 + 150 * Math.sin(2 * Math.PI * .07 * t));

// ---------- accents on the beats ----------
A.whoosh(T.card - .2, .8, .045);
T.items.forEach((t, k) => A.pluck(t, [440, 523.25, 659.25][k % 3], .05));
A.whoosh(T.end - 1, .8, .04);
A.bell(T.end + .4, 880, .12);

// ---------- duck under the voice: about -10 dB, 120 ms attack, 450 ms release ----------
if (CUES) {
  const spans = CUES.order.map(id => [CUES.lines[id].t0 - .08, CUES.lines[id].t1 + .1]);
  let g = 1;
  const atk = Math.exp(-1 / (SR * .12)), rel = Math.exp(-1 / (SR * .45));
  for (let i = 0; i < N; i++) {
    const target = spans.some(([a, b]) => i / SR >= a && i / SR <= b) ? .32 : 1;
    g = target + (g - target) * (target < g ? atk : rel);
    L[i] *= g; R[i] *= g;
  }
}
A.master(process.argv[2] || 'music.wav', 0);
