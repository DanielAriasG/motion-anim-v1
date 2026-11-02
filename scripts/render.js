// Renders a motion.js film with headless Chrome, frame by frame, into stills or an H.264 video.
//   node render.js stills <page.html> <out dir> t1 t2 ...        PNG stills at those times (seconds)
//   node render.js video  <page.html> <out.mp4> [audio.wav]      the whole film (length = window.TOTAL)
// Needs: Chrome or Edge, ffmpeg on PATH, and puppeteer-core (npm i puppeteer-core in the project folder).
// Env: CHROME=<path> to pick the browser; FPS (default 60); FRAME=jpeg for faster, slightly softer frames.
// Frames go to ffmpeg losslessly (PNG) with x264 -tune animation: sharp edges on flat graphics, type and logos.
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const puppeteer = require(require.resolve('puppeteer-core', { paths: [process.cwd(), __dirname] }));

const FPS = parseInt(process.env.FPS || '60', 10), FRAME = process.env.FRAME || 'png';
const CANDIDATES = [process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
const CHROME = CANDIDATES.find(p => p && fs.existsSync(p));
if (!CHROME) throw new Error('no Chrome/Edge found: set CHROME=<path to browser>');

(async () => {
  const [mode, page, out, ...rest] = process.argv.slice(2);
  if (!['stills', 'video'].includes(mode) || !page || !out) throw new Error('usage: render.js stills|video <page.html> <out> ...');
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: true, args: ['--allow-file-access-from-files'] });
  const tab = await browser.newPage();
  let failed = false;
  tab.on('pageerror', e => { failed = true; console.error('page error:', e.message); });
  await tab.setViewport({ width: 1920, height: 1080 });
  await tab.goto('file://' + path.resolve(page).split(path.sep).join('/'), { waitUntil: 'networkidle0' });
  if (failed) { await browser.close(); process.exit(1); }
  await tab.evaluate(() => window.ready);
  const info = await tab.evaluate(() => ({ total: window.TOTAL, fonts: window.FONTS_USED }));
  console.log('fonts', JSON.stringify(info.fonts), 'total', info.total, 's');
  const grab = (t, type) => tab.evaluate((t, type) => {
    window.renderFrame(t);
    return document.getElementById('c').toDataURL(type, .96).split(',')[1];
  }, t, type);

  if (mode === 'stills') {
    fs.mkdirSync(out, { recursive: true });
    for (const s of rest) fs.writeFileSync(path.join(out, `t_${s}.png`), Buffer.from(await grab(parseFloat(s), 'image/png'), 'base64'));
    console.log(rest.length, 'stills ->', out);
  } else {
    const wav = rest[0];
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS),
      '-c:v', FRAME === 'png' ? 'png' : 'mjpeg', '-i', '-', ...(wav ? ['-i', wav] : []),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-tune', 'animation', '-pix_fmt', 'yuv420p',
      ...(wav ? ['-c:a', 'aac', '-b:a', '256k', '-shortest'] : []), '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    const n = Math.round(FPS * info.total);
    for (let f = 0; f < n; f++) {
      const buf = Buffer.from(await grab(f / FPS, 'image/' + FRAME), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % (FPS * 10) === 0) console.log(`frame ${f}/${n}`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    console.log('video ->', out);
  }
  await browser.close();
  if (failed) process.exit(1);
})();
