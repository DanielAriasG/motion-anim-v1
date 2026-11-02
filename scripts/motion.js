// Motion Anim V1 · design engine for deterministic canvas films (1920x1080).
// Load order in the page: [theme.js] [cues.js | beats.js] motion.js film.js
//   theme.js  optional, sets window.THEME (palette, roles, fonts, logo) and may push image decodes onto
//             window.THEME_PRELOAD; default is Apple's system look
//   cues.js   narration timeline from build_timeline.js (CUES); or beats.js with window.BEATS = { name: seconds }
// The film defines drawScene(t) and calls defineFilm({ scene, preload }). render.js calls window.renderFrame(t).
// Everything is a pure function of t: never keep state between frames (frames are rendered out of order).

const W = 1920, H = 1080;
const cv = document.getElementById('c');
const ctx = cv.getContext('2d');

// ---------- theme ----------
// Default: Apple system colours (iOS light values; Apple may adjust them between releases, so treat them
// as a starting point) on the grouped background, white cards, black text.
const DEFAULT_THEME = {
  colors: {
    blue: '#007AFF', green: '#34C759', red: '#FF3B30', orange: '#FF9500', yellow: '#FFCC00', teal: '#30B0C7',
    indigo: '#5856D6', purple: '#AF52DE', pink: '#FF2D55',
    gray: '#8E8E93', gray3: '#C7C7CC', gray5: '#E5E5EA', gray6: '#F2F2F7',
    secondary: '#6E6E73', link: '#0066CC', white: '#FFFFFF', black: '#000000',
  },
  // derived tints (mixed with white) and shades (mixed with black): name: ['tint'|'shade', colour, amount]
  derive: {
    blue50: ['tint', 'blue', .9], blue100: ['tint', 'blue', .8], green50: ['tint', 'green', .88],
    red50: ['tint', 'red', .9], orange50: ['tint', 'orange', .88], teal50: ['tint', 'teal', .88], indigo50: ['tint', 'indigo', .9],
  },
  roles: { canvas: 'gray6', surface: 'white', ink: 'black', secondary: 'secondary', hair: 'gray5', shadow: 'black' },
  // text colour on a fill; anything missing is chosen by contrast. Apple puts white on its saturated fills
  // (3.5-5.6:1, so keep that text bold or large).
  on: { blue: 'white', red: 'white', pink: 'white', purple: 'white', indigo: 'white', secondary: 'white', link: 'white' },
  fonts: {
    display: ['SF Pro Display', 'Segoe UI Variable Display', 'Inter', 'Helvetica Neue', 'Arial'],
    text: ['SF Pro Text', 'Segoe UI Variable Text', 'Inter', 'Helvetica Neue', 'Arial'],
    mono: ['SF Mono', 'Cascadia Mono', 'Consolas', 'Menlo', 'Courier New'],
  },
  logo: null,          // { src, w, h, x, y } drawn unaltered on every frame
  margin: 120,
  requireFonts: false, // true: throw if no listed family is installed (instead of a generic fallback)
};
const THEME = Object.assign({}, DEFAULT_THEME, window.THEME || {});
const M = THEME.margin;

const hexRGB = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const RGB = {};
for (const [k, h] of Object.entries(THEME.colors)) RGB[k] = hexRGB(h);
for (const [k, [kind, base, amt]] of Object.entries(THEME.derive || {}))
  RGB[k] = RGB[base].map(v => Math.round(kind === 'tint' ? v + (255 - v) * amt : v * (1 - amt)));
RGB.white = RGB.white || [255, 255, 255]; RGB.black = RGB.black || [0, 0, 0];   // text on fills is always one of these
const role = r => THEME.roles[r] || r;
const col = (name, a = 1) => { const c = RGB[role(name)]; if (!c) throw new Error('colour not in theme: ' + name); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; };
const lum = c => { const f = v => (v /= 255) <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
const contrast = (a, b) => { const x = lum(RGB[role(a)]), y = lum(RGB[role(b)]); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
// white or black text on a fill: the theme's rule if it has one, else whichever contrasts more
const ON = new Proxy({}, { get: (_, k) => THEME.on[k] || (contrast('white', k) >= contrast('black', k) ? 'white' : 'black') });

// ---------- type: first installed family from each list ----------
function installed(fam) {
  const probe = 'mmmmmmmmmmlli WWW 0123', m = f => { ctx.font = f; return ctx.measureText(probe).width; };
  return m(`72px "${fam}", monospace`) === m(`72px "${fam}", serif`);
}
const FAM = {};
for (const k of ['display', 'text', 'mono']) {
  FAM[k] = THEME.fonts[k].find(installed);
  if (!FAM[k]) { if (THEME.requireFonts) throw new Error('no installed font for ' + k + ': ' + THEME.fonts[k].join(', ')); FAM[k] = k === 'mono' ? 'monospace' : 'sans-serif'; }
}
window.FONTS_USED = FAM;
const q = f => /^(monospace|sans-serif|serif)$/.test(f) ? f : `"${f}"`;
const FD = (s, w = 600) => `${w} ${s}px ${q(FAM.display)}`;
const FT = (s, w = 400) => `${w} ${s}px ${q(FAM.text)}`;
const FM = (s, w = 400) => `${w} ${s}px ${q(FAM.mono)}`;
function text(str, x, y, font, color = 'ink', a = 1, ls = 0, align = 'left') {
  ctx.font = font; ctx.letterSpacing = ls + 'px'; ctx.textAlign = align;
  ctx.fillStyle = color.startsWith('rgba') ? color : col(color, a); ctx.fillText(str, x, y);
  ctx.textAlign = 'left';
}
function measure(str, font, ls = 0) {
  ctx.save(); ctx.font = font; ctx.letterSpacing = ls + 'px';
  const w = ctx.measureText(str).width; ctx.restore(); return w;
}
function wrapLines(str, font, maxW) {
  const lines = [''];
  for (const w of str.split(' ')) {
    const t = lines[lines.length - 1] ? lines[lines.length - 1] + ' ' + w : w;
    if (measure(t, font) > maxW && lines[lines.length - 1]) lines.push(w); else lines[lines.length - 1] = t;
  }
  return lines;
}

// ---------- motion: critically damped springs (no bounce), brief and precise ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, p) => a + (b - a) * p;
const spring = x => x <= 0 ? 0 : x >= 1 ? 1 : (1 - (1 + 9 * x) * Math.exp(-9 * x)) / (1 - 10 * Math.exp(-9));
const easeIO = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
// progress 0..1 of a move that starts at s and lasts d
const P = (t, s, d, e = spring) => e(clamp((t - s) / d));
// visible between a and b, with fades in and out
const vis = (t, a, b = Infinity, din = .5, dout = .4) => Math.min(P(t, a, din), 1 - P(t, b, dout, easeIO));

// ---------- timing: narration cues or fixed beats ----------
const CUE = typeof CUES !== 'undefined' ? CUES : null;
const BEAT = window.BEATS || {};
const TOTAL = CUE ? CUE.TOTAL : (window.DURATION || 20);
const norm = s => s.toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9'*-]/g, '');
function lineOf(id) { if (!CUE) throw new Error('no narration (cues.js) loaded'); const L = CUE.lines[id]; if (!L) throw new Error('no narration line ' + id); return L; }
const lineStart = id => lineOf(id).t0, lineEnd = id => lineOf(id).t1;
// start time of the n-th spoken word in line id that matches `word` (case and punctuation ignored)
function cue(id, word, n = 1) {
  const k = norm(word);
  for (const w of lineOf(id).words) if (norm(w.w) === k || norm(w.w).replace(/'s$/, '') === k) { if (--n === 0) return w.s; }
  throw new Error(`cue: "${word}" not in ${id}`);
}
// the words of `str` matched in order to line id's spoken words (from the first match at or after `after`)
function spoken(str, id, after = -Infinity) {
  const ws = lineOf(id).words, out = [];
  let i = ws.findIndex(w => w.s >= after && norm(w.w) === norm(str.split(' ')[0]));
  if (i < 0) throw new Error(`spoken: "${str}" not in ${id}`);
  for (const part of str.split(' ')) {
    while (i < ws.length && norm(ws[i].w) !== norm(part)) i++;
    if (i >= ws.length) throw new Error(`spoken: "${part}" of "${str}" not in ${id}`);
    out.push({ w: part, t: ws[i].s }); i++;
  }
  return out;
}
function beat(name) { if (!(name in BEAT)) throw new Error('no beat ' + name); return BEAT[name]; }
// how long unnarrated text needs on screen: 1 s + 1 s per 3 words, at least 2.5 s
const readTime = str => Math.max(2.5, 1 + str.split(/\s+/).length / 3);
// all words of a string at one time (for text that is not spoken)
const at = (str, t0, c) => str.split(' ').map((w, i) => ({ w, t: t0 + i * .05, c }));

// ---------- text that builds word by word (each word fades up out of a short blur at its time) ----------
// lines: [[{ w, t, c? }...], ...]
function buildText(lines, x, y, font, size, lh, t, { color = 'ink', out = Infinity, align = 'left', ls = 0 } = {}) {
  const qo = P(t, out, .45, easeIO);
  if (qo >= 1) return;
  const sp = measure(' ', font, ls);
  lines.forEach((ws, li) => {
    const total = ws.reduce((a, w) => a + measure(w.w, font, ls), 0) + sp * (ws.length - 1);
    let cx = align === 'center' ? x - total / 2 : x;
    for (const w of ws) {
      const p = P(t, w.t - .04, .5), ww = measure(w.w, font, ls);
      if (p > 0) {
        ctx.save();
        const blur = (1 - p) * 10 + qo * 8;
        if (blur > .3) ctx.filter = `blur(${blur.toFixed(1)}px)`;
        text(w.w, cx, y + li * lh + (1 - p) * size * .22 - qo * size * .12, font, w.c || color, p * (1 - qo), ls);
        ctx.restore();
      }
      cx += ww + sp;
    }
  });
}
// a value that changes in place: the old one slides up and fades, the new one rises in
function swapText(a, b, x, y, fa, fb, ca, cb, p) {
  if (p < 1) text(a, x, y - p * 18, fa, ca, 1 - p);
  if (p > 0) text(b, x, y + (1 - p) * 18, fb, cb, p);
}

// ---------- surfaces ----------
// card: rounded rectangle with a soft two-layer shadow; lift > 1 for an element raised above the rest
function card(x, y, w, h, { r = 28, fill = 'surface', a = 1, lift = 1 } = {}) {
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a;
  ctx.shadowColor = col('shadow', .10 * lift); ctx.shadowBlur = 48 * lift; ctx.shadowOffsetY = 18 * lift;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fillStyle = col(fill); ctx.fill();
  ctx.shadowColor = col('shadow', .07); ctx.shadowBlur = 3; ctx.shadowOffsetY = 1; ctx.fill();
  ctx.restore();
}
function rrect(x, y, w, h, r, fill, a = 1) {
  if (a <= 0 || w <= 0 || h <= 0) return;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, Math.min(r, h / 2, w / 2)); ctx.fillStyle = col(fill, a); ctx.fill();
}
function ring(x, y, w, h, r, color, lw = 3, a = 1) {
  if (a <= 0) return;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.strokeStyle = col(color, a); ctx.lineWidth = lw; ctx.stroke();
}
// capsule label centred on y; p scales it in from 92 % with a fade. Use bold (700) when the fill/text
// contrast is only about 3:1.
function pill(str, x, y, font, size, fill, p = 1, { padX = 14, h = size * 1.7, align = 'left' } = {}) {
  if (p <= 0) return 0;
  const w = measure(str, font) + padX * 2, x0 = align === 'center' ? x - w / 2 : x;
  ctx.save(); ctx.globalAlpha *= clamp(p);
  ctx.translate(x0 + w / 2, y); ctx.scale(lerp(.92, 1, p), lerp(.92, 1, p)); ctx.translate(-(x0 + w / 2), -y);
  rrect(x0, y - h / 2, w, h, h / 2, fill);
  text(str, x0 + padX, y + size * .36, font, ON[role(fill)]);
  ctx.restore();
  return w;
}
function dot(x, y, r, color, a = 1) { if (r <= 0) return; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = col(color, a); ctx.fill(); }
// check mark in a filled circle, drawn on as p goes 0 -> 1
function check(x, y, r, fill, p) {
  if (p <= 0) return;
  dot(x, y, r * lerp(.6, 1, p), fill, p);
  ctx.save();
  ctx.beginPath(); ctx.moveTo(x - r * .42, y + r * .02); ctx.lineTo(x - r * .1, y + r * .34); ctx.lineTo(x + r * .45, y - r * .3);
  ctx.strokeStyle = ON[role(fill)] === 'white' ? '#fff' : '#000'; ctx.lineWidth = r * .2; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.setLineDash([r * 1.6]); ctx.lineDashOffset = r * 1.6 * (1 - P(p, .35, .65, easeIO)); ctx.stroke();
  ctx.restore();
}
// padlock; c = 0 open (shackle lifted), 1 closed
function padlock(x, y, s, color, c, a = 1) {
  ctx.save(); ctx.globalAlpha *= a;
  rrect(x - s * .5, y - s * .1, s, s * .78, s * .16, color);
  const r = s * .3, lift = (1 - c) * s * .28, top = y - s * .36 - lift;
  ctx.beginPath(); ctx.moveTo(x - r, y - s * .05); ctx.lineTo(x - r, top); ctx.arc(x, top, r, Math.PI, 0);
  ctx.lineTo(x + r, c >= 1 ? y - s * .05 : top + s * .1);
  ctx.strokeStyle = col(color); ctx.lineWidth = s * .13; ctx.lineCap = 'round'; ctx.stroke();
  ctx.restore();
}
function bez(p0, p1, p2, p3, u) {
  const v = 1 - u;
  return [0, 1].map(j => v * v * v * p0[j] + 3 * v * v * u * p1[j] + 3 * v * u * u * p2[j] + u * u * u * p3[j]);
}
// draw the part of a cubic bezier between u0 and u1 (0..1)
function strokeBez(pts, u0, u1, color, w = 3, a = 1) {
  if (u1 <= u0) return;
  ctx.beginPath();
  for (let k = 0; k <= 60; k++) { const p = bez(...pts, lerp(u0, u1, k / 60)); k ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]); }
  ctx.strokeStyle = col(color, a); ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.stroke();
}

// ---------- logo and frame shell ----------
const LOGO_IMG = THEME.logo ? Object.assign(new Image(), { src: THEME.logo.src }) : null;
// a < 1 steps it aside (e.g. on an intro or credits card that shows the logo large: one logo per frame)
function drawLogo(t, a = 1) {
  if (!LOGO_IMG || a <= 0) return;
  const L = THEME.logo;
  ctx.save(); ctx.globalAlpha = P(t, .1, .8) * a;
  ctx.drawImage(LOGO_IMG, L.x ?? M, L.y ?? 56, L.w, L.h);   // exact size: never scaled or recoloured
  ctx.restore();
}
// film = { scene(t), preload: [promises], logo(t) -> corner logo alpha 0..1 (optional) }
function defineFilm(film) {
  window.renderFrame = function (t) {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.filter = 'none'; ctx.globalAlpha = 1; ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = col('canvas'); ctx.fillRect(0, 0, W, H);
    film.scene(t);
    drawLogo(t, film.logo ? film.logo(t) : 1);
  };
  window.TOTAL = TOTAL;
  window.ready = (async () => {
    await Promise.all([document.fonts.load(FD(60)), document.fonts.load(FT(20)), document.fonts.load(FM(20)),
      ...(LOGO_IMG ? [LOGO_IMG.decode()] : []), ...(window.THEME_PRELOAD || []), ...(film.preload || [])]);
    window.renderFrame(0);
    return true;
  })();
}
