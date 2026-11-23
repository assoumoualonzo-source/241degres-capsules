"""Nettoie un enregistrement de référence : réduction de bruit (profil pris sur le début),
porte de bruit pour couper les queues de réverbération, suppression des longs silences."""
import subprocess, sys
import numpy as np, noisereduce as nr, soundfile as sf
src, dst = sys.argv[1], sys.argv[2]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "22050", "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
y = np.frombuffer(raw, np.float32).copy()
sr = 22050
# profil de bruit : la fenêtre de 0,5 s la plus calme parmi les 10 premières secondes
w = sr // 2
seg = min(range(0, min(len(y), 10 * sr) - w, w // 2), key=lambda i: np.sqrt(np.mean(y[i:i + w] ** 2)))
y = nr.reduce_noise(y=y, sr=sr, y_noise=y[seg:seg + w], prop_decrease=0.85, stationary=True)
sf.write("/tmp/rec/denoised.wav", y, sr)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "/tmp/rec/denoised.wav", "-af",
                "highpass=f=75,agate=threshold=0.015:ratio=4:attack=3:release=90:range=0.06,"
                "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=-1:stop_duration=0.4:stop_threshold=-45dB,"
                "loudnorm=I=-18:TP=-2", "-ar", "22050", dst], check=True)
