# Estimates word timings for a narration clip that came without them (Fish Audio, OpenAI TTS, a
# recorded voice...). No account or model needed: ffmpeg finds the pauses, and the script's words are
# spread over the speech between them in proportion to their length.
#   python align_estimate.py clip.wav "The exact text that was spoken." > clip.json
# Writes the timing format the pipeline uses: { engine, dur, words: [{ w, s, e }] } (seconds).
# Measured against ElevenLabs timestamps on 9 lines (127 words): median error 0.06 s, 90 % of words within
# 0.17 s, worst 0.72 s. Fine for word-by-word titles; for tighter sync use real timestamps
# (references/narration.md). Optional tuning: [extra weight for a word before punctuation, default 1.0]
# [penalty for a pause that is not after punctuation, default 0.6].
import json, re, subprocess, sys

wav, text = sys.argv[1], sys.argv[2]
NOISE, MIN_GAP = '-35dB', 0.12
PUNCT_EXTRA, MID_PHRASE_PENALTY = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0, float(sys.argv[4]) if len(sys.argv) > 4 else .6

dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav],
                           capture_output=True, text=True).stdout)
log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', wav, '-af', f'silencedetect=n={NOISE}:d={MIN_GAP}',
                      '-f', 'null', '-'], capture_output=True, text=True).stderr
starts = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
ends = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
# speech segments = complement of the silences
sil = list(zip(starts, ends + [dur] * (len(starts) - len(ends))))
segs, t = [], 0.0
for a, b in sil:
    if a - t > .05: segs.append([t, a])
    t = b
if dur - t > .05: segs.append([t, dur])
if not segs: segs = [[0.0, dur]]

words = text.split()
# weight: letters plus a little for each word boundary; a word before punctuation is drawn out
# (phrase-final lengthening), so it counts for more
weight = [len(re.sub(r'[^\w]', '', w)) + 1.5 + (PUNCT_EXTRA if re.search(r'[.,;:?!]$', w) else 0) for w in words]
total_w, speech = sum(weight), sum(b - a for a, b in segs)

# Each pause between speech segments sits at some word boundary. Choose the boundaries by dynamic
# programming: a segment's share of the speech time should match its share of the word weight, and
# boundaries after punctuation are preferred (speakers pause there).
groups = None
n, m = len(words), len(segs)
if 1 < m <= n:
    seg_share = [(b - a) / speech for a, b in segs]
    pref = [0.0]
    for w in weight: pref.append(pref[-1] + w / total_w)
    punct = [bool(re.search(r'[.,;:?!]$', w)) for w in words]
    INF = float('inf')
    # D[k][j]: best cost with segments 0..k-1 covering words 0..j-1
    D = [[INF] * (n + 1) for _ in range(m + 1)]; B = [[0] * (n + 1) for _ in range(m + 1)]
    D[0][0] = 0.0
    for k in range(1, m + 1):
        for j in range(k, n - (m - k) + 1):
            for i in range(k - 1, j):
                if D[k - 1][i] == INF: continue
                c = D[k - 1][i] + ((pref[j] - pref[i]) - seg_share[k - 1]) ** 2 * 50
                if k < m and not punct[j - 1]: c += MID_PHRASE_PENALTY   # a pause mid-phrase is allowed but less likely
                if c < D[k][j]: D[k][j], B[k][j] = c, i
    if D[m][n] < INF:
        bounds, j = [n], n
        for k in range(m, 0, -1): j = B[k][j]; bounds.append(j)
        bounds = bounds[::-1]
        groups = [list(range(bounds[k], bounds[k + 1])) for k in range(m)]
if not groups:
    # one stream over all speech time
    out, acc = [], 0.0
    def at(x):  # speech-time -> clip time
        for a, b in segs:
            if x <= b - a: return a + x
            x -= b - a
        return segs[-1][1]
    for w, wt in zip(words, weight):
        s = at(acc / total_w * speech); acc += wt; e = at(acc / total_w * speech)
        out.append({'w': w, 's': round(s, 3), 'e': round(e, 3)})
else:
    out = []
    for (a, b), idx in zip(segs, groups):
        gw = sum(weight[i] for i in idx); acc = 0.0
        for i in idx:
            s = a + acc / gw * (b - a); acc += weight[i]; e = a + acc / gw * (b - a)
            out.append({'w': words[i], 's': round(s, 3), 'e': round(e, 3)})
json.dump({'engine': 'estimate', 'dur': dur, 'words': out}, sys.stdout, indent=1)
