// Captions from a narrated film's cues.js (the narration's word timings): one SubRip (.srt) file.
//   node make_captions.js <film dir> <out.srt>
// A caption is one sentence on up to two lines of at most 42 characters. A sentence that would fill both lines
// splits at its clause break nearest the middle; lines prefer clause breaks and never end on a little word.
// A line in narration.json may set "captions": ["chunk", ...] to choose the breaks by hand (each chunk is one
// caption, still wrapped and split if too long), e.g. so a name is not left alone on a caption.
// A caption shows from its first word to 0.35 s after its last (at least 1 s), never overlapping the next.
// make_film.py calls this after the render and muxes the result into the MP4 as a switchable subtitle track.
const fs = require('fs');
const path = require('path');

const [dir, out] = process.argv.slice(2);
const CUES = require(path.resolve(dir, 'cues.js'));
const NARR = fs.existsSync(path.join(dir, 'narration.json')) ? JSON.parse(fs.readFileSync(path.join(dir, 'narration.json'), 'utf8')) : { lines: [] };
const CHUNKS = Object.fromEntries(NARR.lines.filter(L => L.captions).map(L => [L.id, L.captions]));

const LINE = 42, HOLD = .35, MIN = 1.0;
const SMALL = /^(the|a|an|of|to|its|and|or|into|may|for|on|in|at|by|with)$/i;
const str = ws => ws.map(w => w.w).join(' ');
const twoLines = ws => ws.some((_, i) => i && str(ws.slice(0, i)).length <= LINE && str(ws.slice(i)).length <= LINE);

// split a sentence into pieces that fit two lines, at the clause break (else word break) nearest its middle;
// a sentence that would fill both lines to the edge splits too: it reads as a wall
function fit(ws) {
  const n = str(ws).length;
  if (n <= LINE || (n <= 2 * LINE - 8 && twoLines(ws))) return [ws];
  let best = 0, bestD = Infinity;
  ws.forEach((w, i) => {
    if (i === ws.length - 1) return;
    const d = Math.abs(str(ws.slice(0, i + 1)).length - n / 2) - (/[,;:]$/.test(w.w) ? 1000 : 0);
    if (d < bestD) { bestD = d; best = i; }
  });
  return [...fit(ws.slice(0, best + 1)), ...fit(ws.slice(best + 1))];
}
// two balanced lines; a clause break wins unless it leaves a line under 30% of the caption
function wrap(ws) {
  if (str(ws).length <= LINE) return str(ws);
  let best = 1, bestD = Infinity;
  for (let i = 1; i < ws.length; i++) {
    const a = str(ws.slice(0, i)).length, b = str(ws.slice(i)).length;
    if (a > LINE || b > LINE) continue;
    const d = Math.abs(a - b) - (/[,;:]$/.test(ws[i - 1].w) && Math.min(a, b) >= .3 * (a + b) ? 20 : 0)
      + (SMALL.test(ws[i - 1].w) ? 10 : 0);
    if (d < bestD) { bestD = d; best = i; }
  }
  return str(ws.slice(0, best)) + '\n' + str(ws.slice(best));
}

const caps = [];
for (const id of CUES.order) {
  if (CHUNKS[id]) {   // breaks chosen by hand: count each chunk's words off the spoken words
    let i = 0;
    for (const chunk of CHUNKS[id]) {
      const ws = CUES.lines[id].words.slice(i, i += chunk.split(/\s+/).filter(Boolean).length);
      if (ws.length) for (const part of fit(ws)) caps.push({ s: part[0].s, e: part[part.length - 1].e, text: wrap(part) });
    }
    continue;
  }
  let sent = [];
  CUES.lines[id].words.forEach((w, i, all) => {
    sent.push(w);
    if (/[.?!]["”’)]?$/.test(w.w) || i === all.length - 1) {
      for (const ws of fit(sent)) caps.push({ s: ws[0].s, e: ws[ws.length - 1].e, text: wrap(ws) });
      sent = [];
    }
  });
}
caps.forEach((c, i) => {
  const next = caps[i + 1] ? caps[i + 1].s - .05 : Infinity;
  c.e = Math.min(Math.max(c.e + HOLD, c.s + MIN), next);
});
const ts = t => {
  const ms = Math.round(t * 1000), p = (v, n = 2) => String(v).padStart(n, '0');
  return `${p(Math.floor(ms / 3600000))}:${p(Math.floor(ms / 60000) % 60)}:${p(Math.floor(ms / 1000) % 60)},${p(ms % 1000, 3)}`;
};
fs.writeFileSync(out, caps.map((c, i) => `${i + 1}\n${ts(c.s)} --> ${ts(c.e)}\n${c.text}\n`).join('\n'), 'utf8');
const long = caps.flatMap(c => c.text.split('\n')).filter(l => l.length > LINE);
console.log(`${caps.length} captions -> ${out}` + (long.length ? `  (${long.length} lines over ${LINE} chars: one word too long to wrap)` : ''));
