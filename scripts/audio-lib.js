// Small synth for film scores (pad, ticks, plucks, latch, whoosh, sub, bell, Schroeder reverb), no samples.
// DUR (seconds) comes from the environment; master() writes a 24-bit stereo WAV normalised to -1.5 dBFS.
const fs = require('fs');

const SR = 48000, DUR = parseFloat(process.env.DUR || '20'), N = Math.round(SR * DUR);
const L = new Float32Array(N), R = new Float32Array(N);
const sendL = new Float32Array(N), sendR = new Float32Array(N); // reverb bus

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const sine = t => -(Math.cos(Math.PI * t) - 1) / 2;
const ramp = (t, s, d) => sine(clamp((t - s) / d));
const bump = (t, c, w) => Math.exp(-Math.pow((t - c) / w, 2));
let seed = 7;
const rnd = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const noise = () => rnd() * 2 - 1;

function add(i, l, r, send = 0) {
  if (i < 0 || i >= N) return;
  L[i] += l; R[i] += r; sendL[i] += l * send; sendR[i] += r * send;
}
function bandpass(f, q) {
  const w = 2 * Math.PI * f / SR, al = Math.sin(w) / (2 * q), a0 = 1 + al;
  return { b0: al / a0, b2: -al / a0, a1: -2 * Math.cos(w) / a0, a2: (1 - al) / a0, x1: 0, x2: 0, y1: 0, y2: 0 };
}
function retune(bq, f, q) { const c = bandpass(f, q); bq.b0 = c.b0; bq.b2 = c.b2; bq.a1 = c.a1; bq.a2 = c.a2; }
function run(bq, x) {
  const y = bq.b0 * x + bq.b2 * bq.x2 - bq.a1 * bq.y1 - bq.a2 * bq.y2;
  bq.x2 = bq.x1; bq.x1 = x; bq.y2 = bq.y1; bq.y1 = y; return y;
}

// ---------- pad ----------
// voices: [{ f, w: t => weight, g }]; env(t) overall level; cutoff(t) in Hz; level per voice
function pad(voices, env, cutoff, level = .028, maxH = 24) {
  const BLOCK = 256;
  for (const v of voices) {
    for (const det of [-6, 6]) {
      const f = v.f * Math.pow(2, det / 1200);
      const pan = det < 0 ? .3 : .7;
      const H = Math.max(1, Math.min(maxH, Math.floor(7000 / f)));
      const ph = Array.from({ length: H }, () => rnd() * Math.PI * 2);
      for (let b = 0; b < N; b += BLOCK) {
        const t = b / SR, w = v.w(t) * env(t);
        if (w < 1e-4) continue;
        const fc = cutoff(t);
        const amps = [];
        for (let h = 1; h <= H; h++) { const x = h * f / fc; amps.push(1 / h / Math.sqrt(1 + x * x * x * x)); }
        const g = level * (v.g ?? 1) * w;
        for (let i = b; i < Math.min(N, b + BLOCK); i++) {
          const tt = i / SR; let s = 0;
          for (let h = 1; h <= H; h++) s += amps[h - 1] * Math.sin(2 * Math.PI * h * f * tt + ph[h - 1]);
          add(i, s * g * (1 - pan) * 2, s * g * pan * 2, .25);
        }
      }
    }
  }
}
// a pure sustained tone with its own envelope (for held notes, hums, plateaus)
function tone(f, env, gain, pan = .5, send = .3, vib = 0) {
  let ph = 0;
  for (let i = 0; i < N; i++) {
    const t = i / SR, e = env(t);
    ph += 2 * Math.PI * f * (1 + vib * Math.sin(2 * Math.PI * 4.5 * t)) / SR;
    if (e < 1e-5) continue;
    const y = Math.sin(ph) * e * gain;
    add(i, y * (1 - pan) * 2, y * pan * 2, send);
  }
}

// ---------- one-shots ----------
function tick(t0, gain = .1, fc = 3000) {
  const bq = bandpass(fc * Math.pow(2, (rnd() - .5) * 2 / 12), 4), pan = .4 + rnd() * .2;
  const s0 = Math.floor(t0 * SR);
  for (let k = 0; k < SR * .04; k++) {
    const e = Math.exp(-k / (SR * .004)), y = run(bq, noise()) * e * gain * 3;
    add(s0 + k, y * (1 - pan), y * pan, .3);
  }
}
function pluck(t0, f, gain = .1, decay = .45) {
  const s0 = Math.floor(t0 * SR);
  for (let k = 0; k < SR * 2; k++) {
    const tt = k / SR, e = Math.min(1, tt / .005) * Math.exp(-tt / decay);
    const y = (Math.sin(2 * Math.PI * f * tt) + .25 * Math.sin(4 * Math.PI * f * tt)) * e * gain;
    add(s0 + k, y, y, .45);
  }
}
function latch(t0) {
  const s0 = Math.floor(t0 * SR);
  let ph = 0;
  for (let k = 0; k < SR * .3; k++) {
    const tt = k / SR, f = 120 + 80 * Math.exp(-tt / .03);
    ph += 2 * Math.PI * f / SR;
    const y = Math.sin(ph) * Math.min(1, tt / .002) * Math.exp(-tt / .05) * .32;
    add(s0 + k, y, y, .2);
  }
  const bq = bandpass(2500, 3), s1 = Math.floor((t0 + .04) * SR);
  for (let k = 0; k < SR * .05; k++) {
    const y = run(bq, noise()) * Math.exp(-k / (SR * .006)) * .5;
    add(s1 + k, y, y, .3);
  }
}
// short filtered thump with a noise skin: a redaction stamp
function stamp(t0, gain = .25) {
  const s0 = Math.floor(t0 * SR);
  let ph = 0;
  for (let k = 0; k < SR * .25; k++) {
    const tt = k / SR, f = 90 + 60 * Math.exp(-tt / .02);
    ph += 2 * Math.PI * f / SR;
    const y = Math.sin(ph) * Math.min(1, tt / .002) * Math.exp(-tt / .06) * gain;
    add(s0 + k, y, y, .15);
  }
  const bq = bandpass(900, 1.2);
  for (let k = 0; k < SR * .08; k++) {
    const y = run(bq, noise()) * Math.exp(-k / (SR * .012)) * gain * .9;
    add(s0 + k, y, y, .25);
  }
}
function whoosh(t0, dur = .7, gain = .07) {
  const s0 = Math.floor(t0 * SR), n = Math.floor(dur * SR);
  const bq = bandpass(300, .8);
  for (let k = 0; k < n; k++) {
    const u = k / n;
    if (k % 64 === 0) retune(bq, 300 * Math.pow(8, u), .8);
    const e = Math.pow(Math.sin(Math.PI * u), 2), y = run(bq, noise()) * e * gain * 2;
    add(s0 + k, y * (1 - u), y * u, .35);
  }
}
function sub(t0, gain = .42) {
  const s0 = Math.floor(t0 * SR);
  let ph = 0;
  for (let k = 0; k < SR * 2; k++) {
    const tt = k / SR, f = 50 + 10 * Math.exp(-tt / .15);
    ph += 2 * Math.PI * f / SR;
    const y = Math.sin(ph) * Math.min(1, tt / .01) * Math.exp(-tt / .5) * gain;
    add(s0 + k, y, y, .1);
  }
}
function bell(t0, fc, gain) {
  const s0 = Math.floor(t0 * SR), fm = fc * 1.4;
  for (let k = 0; k < SR * 3; k++) {
    const tt = k / SR, idx = 2.2 * Math.exp(-tt / .5);
    const e = Math.min(1, tt / .003) * Math.exp(-tt / 1.1);
    const y = Math.sin(2 * Math.PI * fc * tt + idx * Math.sin(2 * Math.PI * fm * tt)) * e * gain;
    add(s0 + k, y * .55, y * .45, .6);
  }
}

// ---------- reverb (Schroeder/Freeverb-style) ----------
function reverb(inp, combs, aps) {
  const out = new Float32Array(N);
  const cs = combs.map(d => ({ buf: new Float32Array(d), i: 0, lp: 0 }));
  const as = aps.map(d => ({ buf: new Float32Array(d), i: 0 }));
  for (let n = 0; n < N; n++) {
    let s = 0;
    for (const c of cs) {
      const y = c.buf[c.i];
      c.lp = y * .7 + c.lp * .3;
      c.buf[c.i] = inp[n] + c.lp * .84;
      c.i = (c.i + 1) % c.buf.length; s += y;
    }
    s /= cs.length;
    for (const a of as) {
      const b = a.buf[a.i], y = -s + b;
      a.buf[a.i] = s + b * .5; a.i = (a.i + 1) % a.buf.length; s = y;
    }
    out[n] = s;
  }
  return out;
}

// reverb, tail-out, normalize to -1.5 dBFS, optional trim (dB) to match film 01's loudness, 24-bit PCM WAV
function master(file, trimDb = 0) {
  const rvL = reverb(sendL, [1557, 1617, 1491, 1422, 1277, 1356], [556, 441]);
  const rvR = reverb(sendR, [1580, 1640, 1514, 1445, 1300, 1379], [579, 464]);
  for (let n = 0; n < N; n++) { L[n] += rvL[n] * .9; R[n] += rvR[n] * .9; }
  let peak = 0;
  for (let n = 0; n < N; n++) {
    const t = n / SR, g = 1 - ramp(t, DUR - .5, .5);
    L[n] *= g; R[n] *= g; peak = Math.max(peak, Math.abs(L[n]), Math.abs(R[n]));
  }
  const norm = Math.pow(10, (-1.5 + trimDb) / 20) / peak;
  const out = Buffer.alloc(44 + N * 6);
  out.write('RIFF', 0); out.writeUInt32LE(36 + N * 6, 4); out.write('WAVE', 8);
  out.write('fmt ', 12); out.writeUInt32LE(16, 16); out.writeUInt16LE(1, 20); out.writeUInt16LE(2, 22);
  out.writeUInt32LE(SR, 24); out.writeUInt32LE(SR * 6, 28); out.writeUInt16LE(6, 32); out.writeUInt16LE(24, 34);
  out.write('data', 36); out.writeUInt32LE(N * 6, 40);
  for (let n = 0, o = 44; n < N; n++) {
    for (const s of [L[n], R[n]]) { out.writeIntLE(Math.round(clamp(s * norm, -1, 1) * 8388607), o, 3); o += 3; }
  }
  fs.writeFileSync(file, out);
  // the raw peak before normalising: mix.js needs it to keep accents rendered alone at their level in the score
  fs.writeFileSync(file + '.peak.json', JSON.stringify({ peak }));
  console.log('peak', peak.toFixed(3), 'written', file);
}

module.exports = {
  SR, N, DUR, L, R, clamp, sine, ramp, bump, rnd, noise, add, bandpass, retune, run,
  pad, tone, tick, pluck, latch, stamp, whoosh, sub, bell, master,
};
