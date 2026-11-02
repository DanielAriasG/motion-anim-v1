// __TITLE__ · starter film for Motion Anim. Replace the scenes; keep the structure:
//   1. timing (T) from the narration (cue/spoken) or from beats.js
//   2. layout constants
//   3. one draw function per element, each a pure function of t
//   4. drawScene(t) + defineFilm
// Run a still: node ../engine/render.js stills index.html stills 2 5 8

// ---------- 1. timing ----------
const NARRATED = !!CUE;
const T = NARRATED ? {
  title: lineStart('s1'), card: cue('s2', 'each'), items: [cue('s2', 'appears'), cue('s2', 'exactly'), cue('s2', 'said')],
  out: lineStart('end') - .9, end: lineStart('end'),
} : {
  title: beat('title'), card: beat('card'), items: beat('items'), out: beat('end') - .9, end: beat('end'),
};
// words of a title: as spoken, or all at one time when there is no narration
const words = (str, id, t0, paint = {}) => (NARRATED ? spoken(str, id) : at(str, t0)).map(w => ({ ...w, c: paint[w.w] }));

// ---------- 2. layout ----------
const CARD = { x: M, y: 300, w: 1000, h: 480 };

// ---------- 3. elements ----------
// colour keys are the words as written, punctuation included
const TITLE = words('Every film starts with one clear idea.', 's1', T.title, { 'idea.': 'blue' });
function drawTitle(t) {
  buildText([TITLE], M, 210, FD(64, 700), 64, 0, t, { out: T.out });
}
const ITEMS = ['Each part appears', 'exactly when', 'it is said.'];
function drawCard(t) {
  const a = vis(t, T.card, T.out, .7, .5);
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a;   // *=: the card fades with its content, inside the scene fade
  card(CARD.x, CARD.y + (1 - P(t, T.card, .7)) * 30, CARD.w, CARD.h);
  ITEMS.forEach((s, k) => {
    const y = CARD.y + 120 + k * 120, p = P(t, T.items[k], .6);
    check(CARD.x + 70, y - 12, 22, 'green', p);
    text(s, CARD.x + 120, y, FT(40, 600), 'ink', p);
  });
  pill('Synced', CARD.x + CARD.w - 60, CARD.y + 60, FT(20, 700), 20, 'blue', P(t, T.items[2] + .4, .5), { align: 'center' });
  ctx.restore();
}
const END = words('Made with Motion Anim.', 'end', T.end);
function drawEnd(t) {
  if (t < T.out) return;
  buildText([END], M, 500, FD(88, 700), 88, 0, t);
  text('Your source or credit line', M, 580, FT(24), 'secondary', P(t, T.end + 1, .8));
}

// ---------- 4. scene ----------
function drawScene(t) {
  const out = P(t, T.out, .7, easeIO);
  ctx.save();
  if (out > 0) { ctx.globalAlpha = 1 - out; ctx.filter = `blur(${(out * 8).toFixed(1)}px)`; }
  if (out < 1) { drawTitle(t); drawCard(t); }
  ctx.restore();
  drawEnd(t);
}
defineFilm({ scene: drawScene });
