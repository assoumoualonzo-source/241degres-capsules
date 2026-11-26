# 241degres — capsules TikTok automatiques sur l'actualité du Gabon

Pipeline qui transforme un script JSON en vidéo verticale 1080×1920 prête à publier : voix off neuronale, sous-titres mot à mot, chiffres animés, barre de progression, transitions, musique générée et miniature.

## Arborescence
```
pipeline/make.py          générateur vidéo (images → voix → scènes → montage)
episodes/AAAA-MM-JJ-info/ un dossier par capsule (episode.json + out/)
episodes/AAAA-MM-JJ-culture/
episodes/AAAA-MM-JJ-clip-<nom>/ short EXTRAIT (clip.json ; vidéo source hors dépôt)
pipeline/clip.py          générateur des shorts EXTRAIT (transcription Whisper, habillage)
episodes/AAAA-MM-JJ-buzz/ short BUZZ (captures dans shots/, hors dépôt)
tools/capture.py          capture d'écran d'une publication (Playwright)
docs/charte-editoriale.md ligne éditoriale, formats, sources, règles de droits
docs/episode-schema.md    format du fichier episode.json
assets/fonts/             polices libres (OFL)
```

## Installation
```bash
# ffmpeg requis. Installe dépendances, polices (Google Fonts), logo et OpenVoice.
VOICE_SE_JSON='[...]' bash tools/setup.sh   # empreinte vocale fournie hors dépôt
```

## Générer une capsule
```bash
python3 pipeline/make.py episodes/2026-11-23-info --preview   # images de contrôle
python3 pipeline/make.py episodes/2026-11-23-info             # vidéo finale
```
Le dossier `out/` contient `video.mp4`, `cover.jpg` et `post.txt` (légende, hashtags, sources, crédits).

## Automatisation
Deux tâches planifiées Claude :
- **INFO quotidienne** : veille sur l'actualité gabonaise, rédaction du script, rendu, commit.
- **CULTURE un jour sur deux** : même chaîne avec un format culturel tiré de la charte.
- **VEILLE VIDÉOS** (chaque matin) : liste des vidéos de personnalités publiques qui font parler, envoyée à Stéphane.
- **EXTRAITS** (12 h 40 et 17 h 10) : chaque vidéo déposée dans le dossier Drive « 241degres - Clips à traiter » devient un short habillé (`pipeline/clip.py` : sous-titres mot à mot, nom, source).
- Format BUZZ par capture d'écran (`tools/capture.py`) disponible à la demande.

Les vidéos ne sont pas versionnées (`.gitignore`). Seuls les scripts et `post.txt` le sont.
