#!/usr/bin/env python3
"""
Kokoro TTS wrapper for Frontion News podcast generation.

Reads a plain-text file and writes an MP3 using Kokoro-82M with the
bm_george British male voice at speed 1.1.

Uses the isolated venv at local-only/tts-spike/.venv (Kokoro is not
installed in the system Python).

Usage:
    python3 kokoro_tts.py <input.txt> <output.mp3>
"""

import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PY = os.path.join(BASE_DIR, 'local-only', 'tts-spike', '.venv', 'bin', 'python')
FFMPEG = '/opt/homebrew/bin/ffmpeg'

VOICE = 'bm_george'
SPEED = 1.1
SAMPLE_RATE = 24000


def main():
    if len(sys.argv) != 3:
        print('usage: kokoro_tts.py <input.txt> <output.mp3>', file=sys.stderr)
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]
    wav_path = out_path.rsplit('.', 1)[0] + '.wav'

    runner = f'''
import sys
import numpy as np
import soundfile as sf
from kokoro import KPipeline

with open({in_path!r}) as f:
    text = f.read()

pipeline = KPipeline(lang_code='b')
chunks = [audio for _, _, audio in pipeline(text, voice={VOICE!r}, speed={SPEED})]
if not chunks:
    sys.exit('no audio generated')
audio = np.concatenate(chunks)
sf.write({wav_path!r}, audio, {SAMPLE_RATE})
print(f'kokoro: {{len(audio) / {SAMPLE_RATE}:.1f}}s of audio')
'''
    r = subprocess.run([VENV_PY, '-c', runner])
    if r.returncode != 0:
        sys.exit(r.returncode)

    r = subprocess.run([
        FFMPEG, '-y', '-i', wav_path,
        '-codec:a', 'libmp3lame', '-b:a', '128k',
        out_path,
    ], capture_output=True)
    if r.returncode != 0:
        print(r.stderr.decode()[-800:], file=sys.stderr)
        sys.exit(r.returncode)

    os.remove(wav_path)
    print(f'OK {out_path}')


if __name__ == '__main__':
    main()
