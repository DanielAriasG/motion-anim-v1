// Narration with ElevenLabs text-to-speech, with character timestamps -> word timings.
//   ELEVENLABS_API_KEY=... [VOICE_ID=...] node tts_elevenlabs.js <film dir>
// Reads <film dir>/narration.json; writes <film dir>/vo/<id>.wav (48 kHz mono) + <id>.json ({ engine, dur, words }).
// Lines are sent one by one with their neighbours as previous_text / next_text so the prosody runs on.
// Common failures: 401 missing_permissions -> enable "Text to Speech" on the API key;
// 402 paid_plan_required -> library voices need a paid plan, use a premade voice (references/narration.md).
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const dir = path.resolve(process.argv[2] || '.');
const N = JSON.parse(fs.readFileSync(path.join(dir, 'narration.json'), 'utf8'));
const KEY = process.env.ELEVENLABS_API_KEY;
if (!KEY) throw new Error('set ELEVENLABS_API_KEY (never write the key into a file)');
const VOICE = process.env.VOICE_ID || N.voice?.elevenlabs_voice_id || 'Xb7hH8MSUJpSbSDYk0k2';
const MODEL = N.voice?.model_id || 'eleven_multilingual_v2';
const out = path.join(dir, 'vo');
fs.mkdirSync(out, { recursive: true });

function words(al) {
  const res = []; let cur = null;
  al.characters.forEach((c, i) => {
    if (/\s/.test(c)) { if (cur) res.push(cur); cur = null; return; }
    if (!cur) cur = { w: '', s: al.character_start_times_seconds[i] };
    cur.w += c; cur.e = al.character_end_times_seconds[i];
  });
  if (cur) res.push(cur);
  return res;
}

(async () => {
  const L = N.lines;
  for (let i = 0; i < L.length; i++) {
    const body = {
      text: L[i].text, model_id: MODEL,
      previous_text: i ? L[i - 1].text : undefined, next_text: L[i + 1]?.text,
      voice_settings: Object.assign({ stability: .55, similarity_boost: .8, style: .1, use_speaker_boost: true, speed: .95 }, N.voice?.settings),
    };
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/with-timestamps?output_format=mp3_44100_128`, {
      method: 'POST', headers: { 'xi-api-key': KEY, 'Content-Type': 'application/json' }, body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${L[i].id}: HTTP ${r.status} ${await r.text()}`);
    const d = await r.json();
    const mp3 = path.join(out, L[i].id + '.mp3'), wav = path.join(out, L[i].id + '.wav');
    fs.writeFileSync(mp3, Buffer.from(d.audio_base64, 'base64'));
    execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', mp3, '-ar', '48000', '-ac', '1', '-c:a', 'pcm_s24le', wav]);
    const dur = parseFloat(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav]).toString());
    fs.writeFileSync(path.join(out, L[i].id + '.json'), JSON.stringify({ engine: 'elevenlabs', voice: VOICE, dur, words: words(d.alignment) }, null, 1));
    console.log(L[i].id, dur.toFixed(2) + ' s');
  }
})().catch(e => { console.error(e.message); process.exit(1); });
