#!/usr/bin/env bash
# Installe OpenVoice V2 (licence MIT) pour appliquer la voix de Stéphane à la voix off.
set -e
D="${OPENVOICE_DIR:-$HOME/.cache/openvoice}"
mkdir -p "$D"
pip install -q --break-system-packages torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install -q --break-system-packages librosa soundfile huggingface_hub wavmark unidecode inflect eng_to_ipa pypinyin jieba cn2an
[ -d "$D/ov" ] || git clone -q --depth 1 https://github.com/myshell-ai/OpenVoice.git "$D/ov"
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('myshell-ai/OpenVoiceV2', allow_patterns=['converter/*'], local_dir='$D/ckpt')"
echo "OpenVoice prêt dans $D"
