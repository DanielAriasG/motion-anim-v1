# Draft narration with a local Windows voice, same outputs as tts.js (vo/<id>.wav + <id>.json).
#   powershell -ExecutionPolicy Bypass -File tts_sapi.ps1 <film dir>
# Only for checking timing and sync before the ElevenLabs voice is available.
param([string]$Film = ".")
Add-Type -AssemblyName System.Speech
Add-Type -ReferencedAssemblies System.Speech -TypeDefinition @'
using System.Collections.Generic;
using System.Speech.Synthesis;
using System.Speech.AudioFormat;
public static class Say {
  // speaks text to a wav file and returns "word<TAB>start seconds" per word.
  // Written at 16 kHz: SpeakProgress positions are only right at that rate (at 22.05 kHz they run 1.38x long).
  public static List<string> ToWav(string voice, string text, string wav) {
    var marks = new List<string>();
    using (var s = new SpeechSynthesizer()) {
      s.SelectVoice(voice); s.Rate = -1;
      s.SetOutputToWaveFile(wav, new SpeechAudioFormatInfo(16000, AudioBitsPerSample.Sixteen, AudioChannel.Mono));
      s.SpeakProgress += (o, e) => marks.Add(e.Text + "\t" + e.AudioPosition.TotalSeconds.ToString(System.Globalization.CultureInfo.InvariantCulture));
      s.Speak(text);
    }
    return marks;
  }
}
'@
$dir = (Resolve-Path $Film).Path
$voiceName = "Microsoft Zira Desktop"
$n = Get-Content (Join-Path $dir 'narration.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$out = Join-Path $dir 'vo'
New-Item -ItemType Directory -Force $out | Out-Null
foreach ($line in $n.lines) {
  $raw = Join-Path $out ($line.id + '.raw.wav')
  $v = if ($n.voice.sapi_draft) { $n.voice.sapi_draft } else { $voiceName }
  $marks = [Say]::ToWav($v, $line.text, $raw)
  $wav = Join-Path $out ($line.id + '.wav')
  & ffmpeg -y -loglevel error -i $raw -ar 48000 -ac 1 -c:a pcm_s24le $wav
  Remove-Item $raw
  $dur = [double](& ffprobe -v error -show_entries format=duration -of csv=p=0 $wav)
  # a word ends where the next starts (or at the end of the audio, less a short release)
  $words = @()
  for ($i = 0; $i -lt $marks.Count; $i++) {
    $w, $s = $marks[$i] -split "`t"
    $e = if ($i + 1 -lt $marks.Count) { [double](($marks[$i + 1] -split "`t")[1]) - 0.04 } else { $dur - 0.15 }
    $words += [pscustomobject]@{ w = $w; s = [math]::Round([double]$s, 3); e = [math]::Round($e, 3) }
  }
  $json = [pscustomobject]@{ engine = 'sapi-draft'; voice = $v; dur = $dur; words = $words } | ConvertTo-Json -Depth 4
  [IO.File]::WriteAllText((Join-Path $out ($line.id + '.json')), $json)
  Write-Output ("{0} {1:N2} s, {2} words" -f $line.id, $dur, $words.Count)
}
