"""Puts captions into an MP4 as a switchable subtitle track (mov_text); the picture is copied, not re-encoded.
   python attach_captions.py <video.mp4> <captions.srt> <out.mp4> [narration.json]
The track's language comes from narration.json "language" (default en). Captions are not burned in, so
viewers can switch them off and nothing in the frame is covered; platforms that take an .srt get the file.
"""
import json, pathlib, subprocess, sys

video, srt, out = sys.argv[1:4]
lang = 'en'
if len(sys.argv) > 4 and pathlib.Path(sys.argv[4]).exists():
    lang = json.loads(pathlib.Path(sys.argv[4]).read_text(encoding='utf-8')).get('language', 'en')
iso = {'en': 'eng', 'es': 'spa', 'ca': 'cat', 'fr': 'fra', 'de': 'deu', 'it': 'ita', 'pt': 'por', 'nl': 'nld', 'pl': 'pol'}.get(lang, 'und')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', srt, '-map', '0', '-map', '1', '-c', 'copy',
                '-c:s', 'mov_text', '-metadata:s:s:0', f'language={iso}', out], check=True)
print(f'captions ({iso}) -> {out}')
