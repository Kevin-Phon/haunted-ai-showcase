"""Original deterministic sound design; no recordings, models or samples."""
import math
from pathlib import Path
import struct
import wave

DESTINATION = Path(__file__).resolve().parents[1] / "public" / "media"
RATE = 22050


def write(name, duration, sample):
    path = DESTINATION / name
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite {path}")
    with wave.open(str(path), "wb") as track:
        track.setnchannels(1)
        track.setsampwidth(2)
        track.setframerate(RATE)
        track.writeframes(b"".join(
            struct.pack("<h", round(max(-1, min(1, sample(i / RATE))) * 32767))
            for i in range(round(duration * RATE))
        ))


write("manor-ambience-v1.wav", 8, lambda t:
      .045 * math.sin(2 * math.pi * 55 * t)
      + .025 * math.sin(2 * math.pi * 82.5 * t)
      * (.7 + .3 * math.cos(2 * math.pi * t / 8))
      + .012 * math.sin(2 * math.pi * 110 * t))
write("discovery-v1.wav", 1.5, lambda t:
      .1 * min(1, t * 35) * (1 - t / 1.5) ** 3
      * (math.sin(2 * math.pi * 440 * t)
         + .35 * math.sin(2 * math.pi * 660 * t)))
