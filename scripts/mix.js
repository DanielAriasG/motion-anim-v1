// Final soundtrack: voice over the (already ducked) score, normalised for online video.
//   node mix.js <film dir> [music.wav] [mix.wav]
// With narration (vo-track.wav present): voice levelled to -19 LUFS, score 11 LU below it. Without: the score alone.
// With a supplied music file (env BED=bed.wav, from music_file.py): the bed at BED_LUFS (default -34, 15 LU
// under the voice), ducked about 8 dB more while the voice speaks (sidechain, 250 ms down, 800 ms up), plus the
// score's accents (accents.wav, score.js with BED=none) at the level they have in the full score.
// Then two-pass loudnorm to LUFS (env, default -16) integrated, -1.5 dBTP true peak, linear gain.
const path = require('path');
const fs = require('fs');
const { execFileSync, spawnSync } = require('child_process');

const dir = path.resolve(process.argv[2] || '.');
const music = path.resolve(dir, process.argv[3] || 'music.wav'), out = path.resolve(dir, process.argv[4] || 'mix.wav');
const vo = path.join(dir, 'vo-track.wav'), TARGET = parseFloat(process.env.LUFS || '-16');

function measure(file) {
  const s = spawnSync('ffmpeg', ['-hide_banner', '-nostats', '-i', file, '-af', 'ebur128=peak=true', '-f', 'null', '-']).stderr.toString();
  const I = parseFloat(s.match(/I:\s+(-?[\d.]+) LUFS/g).pop().split(/\s+/)[1]);
  const pk = parseFloat((s.match(/Peak:\s+(-?[\d.]+) dBFS/g) || ['Peak: 0']).pop().split(/\s+/)[1]);
  return { I, pk };
}
const pre = out.replace(/\.wav$/, '.pre.wav');
const bed = process.env.BED ? path.resolve(dir, process.env.BED) : null;
if (bed) {
  const accents = path.join(dir, 'accents.wav'), peak = f => JSON.parse(fs.readFileSync(f + '.peak.json', 'utf8')).peak;
  const m = measure(music), b = measure(bed), gm = -30 - m.I + 20 * Math.log10(peak(accents) / peak(music));
  const gb = parseFloat(process.env.BED_LUFS || '-34') - b.I, voiced = fs.existsSync(vo);
  const gv = voiced ? -19 - measure(vo).I : 0;
  console.log(`bed ${b.I} LUFS (${gb.toFixed(1)} dB), accents ${gm.toFixed(1)} dB` + (voiced ? `, voice ${gv.toFixed(1)} dB` : ''));
  const ins = ['-i', bed, '-i', accents].concat(voiced ? ['-i', vo] : []);
  const fc = voiced
    ? `[2]volume=${gv.toFixed(2)}dB,aformat=channel_layouts=stereo,asplit[v][key];` +
      `[0]volume=${gb.toFixed(2)}dB[b0];[b0][key]sidechaincompress=threshold=0.02:ratio=4:attack=250:release=800[b];` +
      `[1]volume=${gm.toFixed(2)}dB[a];[v][b][a]amix=inputs=3:normalize=0:duration=longest[o]`
    : `[0]volume=${gb.toFixed(2)}dB[b];[1]volume=${gm.toFixed(2)}dB[a];[b][a]amix=inputs=2:normalize=0:duration=longest[o]`;
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...ins, '-filter_complex', fc, '-map', '[o]', '-ar', '48000', '-c:a', 'pcm_s24le', pre]);
} else if (fs.existsSync(vo)) {
  const v = measure(vo), m = measure(music), gv = -19 - v.I, gm = -30 - m.I;
  console.log(`voice ${v.I} LUFS (${gv.toFixed(1)} dB), music ${m.I} LUFS (${gm.toFixed(1)} dB)`);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', vo, '-i', music, '-filter_complex',
    `[0]volume=${gv.toFixed(2)}dB,aformat=channel_layouts=stereo[v];[1]volume=${gm.toFixed(2)}dB[m];[v][m]amix=inputs=2:normalize=0:duration=longest[o]`,
    '-map', '[o]', '-ar', '48000', '-c:a', 'pcm_s24le', pre]);
} else fs.copyFileSync(music, pre);
const r1 = spawnSync('ffmpeg', ['-hide_banner', '-i', pre, '-af', `loudnorm=I=${TARGET}:TP=-1.5:LRA=11:print_format=json`, '-f', 'null', '-']).stderr.toString();
const j = JSON.parse(r1.slice(r1.lastIndexOf('{'), r1.lastIndexOf('}') + 1));
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', pre, '-af',
  `loudnorm=I=${TARGET}:TP=-1.5:LRA=11:measured_I=${j.input_i}:measured_TP=${j.input_tp}:measured_LRA=${j.input_lra}:measured_thresh=${j.input_thresh}:offset=${j.target_offset}:linear=true`,
  '-ar', '48000', '-c:a', 'pcm_s24le', out]);
fs.unlinkSync(pre);
const f = measure(out);
console.log(`mix ${f.I} LUFS, peak ${f.pk} dBFS -> ${out}`);
