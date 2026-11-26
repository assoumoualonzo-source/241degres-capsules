#!/usr/bin/env bash
# Prépare une machine neuve : dépendances, polices, logo, OpenVoice.
set -e
cd "$(dirname "$0")/.."
pip install -q --break-system-packages edge-tts opencv-python-headless pillow numpy noisereduce soundfile faster-whisper
F=assets/fonts; mkdir -p "$F"
[ -f "$F/Anton-Regular.ttf" ] || curl -sfL -o "$F/Anton-Regular.ttf" https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf
[ -f "$F/Montserrat[wght].ttf" ] || curl -sfL -o "$F/Montserrat[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
python3 assets/logo/build_logo.py
bash tools/setup_voice.sh
# Empreinte vocale : fournie hors dépôt dans assets/voix/stephane_se.json (variable VOICE_SE_JSON possible)
mkdir -p assets/voix
[ -n "$VOICE_SE_JSON" ] && printf '%s' "$VOICE_SE_JSON" > assets/voix/stephane_se.json
echo "Prêt."
