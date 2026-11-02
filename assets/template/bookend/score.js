// Score for the __KIND__: a soft, bright pad (major, no tension notes) that fades in and out with the picture,
// ducked under the voice when there is one. No accents: a bookend is one sentence.
//   node score.js music.wav
const fs = require('fs');
const path = require('path');
const here = f => path.join(__dirname, f);
const CUES = fs.existsSync(here('cues.js')) ? require('./cues') : null;
const TOTAL = CUES ? CUES.TOTAL : require('./beats').DURATION;
process.env.DUR = String(TOTAL);
const A = require('../../engine/audio-lib');
const { ramp, SR, N, L, R } = A;

const CHORD = [87.31, 174.61, 220.0, 261.63, 392.0];   // F major add9, open voicing
const env = t => ramp(t, 0, 1.5) * (1 - ramp(t, TOTAL - 1.6, 1.5));
A.pad(CHORD.map(f => ({ f, w: () => 1 })), env, t => 1400 + 300 * Math.sin(2 * Math.PI * .08 * t));

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
