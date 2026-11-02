// __KIND__ of "__TITLE__", built from the client's description: the logo large (when the theme has one), one
// sentence in text weight, and a title in the accent colour. With narration each word appears as it is said;
// without, the words build in reading order and hold for their reading time. make_film.py builds this as a
// small film of its own and bookends.py joins it to the film. It is a starting point: restyle it to the brief
// (colours, an image, a different layout), keeping one idea per frame and the logo rule (one logo per frame).
const SENTENCE = __SENTENCE__;   // spoken (narration.json) or shown
const TITLE_STR = __TITLE_STR__; // large, accent colour; '' for none
const ACCENT = 'blue';           // a colour name from the theme
const OUT = TOTAL - .7;          // fades out before the next part's first frame

// the sentence and the title as timed words: when the sentence ends with the title, the title is the tail of
// what is said; otherwise the title follows the sentence
const NARRATED = !!CUE, ID = NARRATED ? CUE.order[0] : null;
const ends = (s, tail) => tail && norm(s.replace(/[.\s]+$/, '')).endsWith(norm(tail.replace(/[.\s]+$/, '')));
const PHRASE_STR = ends(SENTENCE, TITLE_STR)
  ? SENTENCE.replace(/[.\s]+$/, '').slice(0, -TITLE_STR.replace(/[.\s]+$/, '').length).trim() : SENTENCE;
const PHRASE = PHRASE_STR ? (NARRATED ? spoken(PHRASE_STR, ID) : at(PHRASE_STR, .5)) : [];
const t1 = PHRASE.length ? PHRASE[PHRASE.length - 1].t + .5 : .5;
const TITLE_WORDS = !TITLE_STR ? [] : (NARRATED && ends(SENTENCE, TITLE_STR) ? spoken(TITLE_STR, ID, t1 - .5) : at(TITLE_STR, NARRATED ? lineEnd(ID) + .2 : t1))
  .map(w => ({ ...w, c: ACCENT }));

// the logo as the theme sets it, scaled up only when it is a vector (SVG); the corner logo stays off
const LOGO = THEME.logo ? Object.assign(new Image(), { src: THEME.logo.src }) : null;
const LS = THEME.logo && /\.svg$/i.test(THEME.logo.src) ? 1.5 : 1;
function drawBigLogo(t) {
  const p = P(t, .15, .9);
  if (!LOGO || p <= 0) return;
  ctx.save(); ctx.globalAlpha *= p;
  ctx.drawImage(LOGO, M, 210 + (1 - p) * 16, THEME.logo.w * LS, THEME.logo.h * LS);
  ctx.restore();
}

// one line, or two balanced lines that never end on a little word; smaller type if it needs more
const SMALL = /^(of|and|or|the|a|an|to|in|on|for|with|by|at|its)$/i;
const lineW = (ws, font) => measure(ws.map(w => w.w).join(' '), font);
function lay(ws, font) {
  const max = W - 2 * M;
  if (!ws.length || lineW(ws, font) <= max) return [ws];
  let best = null, bestD = Infinity;
  for (let i = 1; i < ws.length; i++) {
    const a = lineW(ws.slice(0, i), font), b = lineW(ws.slice(i), font);
    if (a > max || b > max) continue;
    const d = Math.abs(a - b) + (SMALL.test(ws[i - 1].w) ? max : 0);
    if (d < bestD) { bestD = d; best = i; }
  }
  return best ? [ws.slice(0, best), ws.slice(best)] : null;
}
let L = null;   // laid out on the first frame, once the fonts are loaded
function drawWords(t) {
  if (!L) {
    const ps = [42, 36, 30].find(s => lay(PHRASE, FD(s, 600))) || 30;
    const ts = [76, 64, 54].find(s => lay(TITLE_WORDS, FD(s, 700))) || 54;
    L = { ps, ts, phrase: lay(PHRASE, FD(ps, 600)) || [PHRASE], title: lay(TITLE_WORDS, FD(ts, 700)) || [TITLE_WORDS] };
  }
  const y0 = LOGO ? 460 : 380;
  buildText(L.phrase, M, y0, FD(L.ps, 600), L.ps, L.ps * 1.38, t);
  buildText(L.title, M, y0 + (PHRASE.length ? L.phrase.length * L.ps * 1.38 + 64 : 0), FD(L.ts, 700), L.ts, L.ts * 1.2, t);
}

function drawScene(t) {
  const q = P(t, OUT, .6, easeIO);
  ctx.save();
  if (q > 0) { ctx.globalAlpha = 1 - q; ctx.filter = `blur(${(q * 6).toFixed(1)}px)`; }
  drawBigLogo(t);
  drawWords(t);
  ctx.restore();
}
defineFilm({ scene: drawScene, logo: () => 0, preload: LOGO ? [LOGO.decode()] : [] });
