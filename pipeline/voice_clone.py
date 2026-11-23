"""Applique le timbre de la voix de référence (enregistrement de l'utilisateur) à la voix off de synthèse.
Le filigrane audio d'OpenVoice (marquage IA) reste activé."""
import glob
import os
import subprocess
import sys

import torch

D = os.environ.get("OPENVOICE_DIR", os.path.expanduser("~/.cache/openvoice"))
sys.path.insert(0, os.path.join(D, "ov"))
torch.set_num_threads(2)
from openvoice.api import ToneColorConverter  # noqa: E402

conv = ToneColorConverter(f"{D}/ckpt/converter/config.json", device="cpu")  # filigrane activé par défaut
conv.load_ckpt(f"{D}/ckpt/converter/checkpoint.pth")
src_dir, out_dir, ref = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(out_dir, exist_ok=True)
wavs = []
for f in sorted(glob.glob(f"{src_dir}/[0-9][0-9].mp3")):
    w = os.path.join(out_dir, os.path.basename(f).replace(".mp3", "_src.wav"))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-ac", "1", "-ar", "22050", w], check=True)
    wavs.append(w)
src_se = conv.extract_se(wavs)
if ref.endswith(".json"):  # empreinte vocale précalculée (256 valeurs), pas d'audio brut
    import json
    tgt_se = torch.tensor(json.load(open(ref)), dtype=torch.float32).view(1, 256, 1)
else:
    tgt_se = conv.extract_se([ref])
for w in wavs:
    conv.convert(audio_src_path=w, src_se=src_se, tgt_se=tgt_se, output_path=w.replace("_src.wav", ".wav"), tau=0.3)
    print("ok", w)
