# Format de episode.json

```json
{
  "type": "info | culture",
  "date": "23 NOV. 2026",
  "title": "Titre de publication",
  "voice": "fr-FR-HenriNeural",
  "rate": "+10%",
  "scenes": [ ... ],
  "sources": ["url", "..."],
  "credits": "Photos : Unsplash (auteurs)",
  "hashtags": "#Gabon #241degres ..."
}
```

## Types de scènes (`kind`)
| kind | champs | usage |
|---|---|---|
| hook | kicker, headline | accroche, 2 lignes max |
| brief | kicker, headline, problem, clear, cover | une info : titre + POURQUOI ÇA COMPTE + CONCRÈTEMENT (format INFO quotidien) |
| story | kicker, headline, stat, stat_label | une actu + un chiffre |
| split | kicker, left_title, left, right_title, right | pour vous / pour l'État |
| alert | kicker, headline, bullets[3] (les 2 premières = interdits, la dernière = action) | arnaque, sécurité |
| civic | kicker, headline (3 lignes courtes), question | réflexe citoyen + question |
| cta | kicker, headline, sub | abonnement + commentaires |
| rank | kicker, rank, headline, stat, stat_label | élément de top (culture) |
| screen | kicker, headline, shot, source | capture d'écran créditée d'une publication (short BUZZ) ; `image` facultative (sinon fond flou tiré de la capture) |

Chaque scène a `image` (URL d'une photo libre de droit, portrait de préférence) et `voice` (texte lu). La durée de la scène suit la voix.

## Extrait vidéo (`clip.json`, `pipeline/clip.py`)
Dossier `episodes/AAAA-MM-JJ-clip-<nom>/` contenant `clip.json` (la vidéo source `src.*` et `work/` restent hors dépôt).
```json
{
  "type": "clip",
  "date": "26 NOV. 2026",
  "video": "src.mp4",
  "video_url": "https://drive.google.com/file/d/<id>/view",
  "source_url": "lien de la vidéo d'origine (YouTube, Facebook, site du média…)",
  "start": "12:30.5", "end": "13:05",
  "speaker": "Prénom Nom", "role": "Fonction exacte",
  "kicker": "ENTRETIEN", "headline": "« LA PHRASE\nFORTE »", "cover_title": "« LA PHRASE\nFORTE »",
  "source": "Gabon 24 · 25/11/2026",
  "question": "Et toi, tu en penses quoi ?",
  "zoom": 1.15, "cover_at": 0.35,
  "fix": {"mot mal transcrit": "mot juste"},
  "title": "…", "hashtags": "…", "sources": ["…"], "credits": "Extrait : <média>"
}
```
- `python3 pipeline/clip.py <dossier> --transcribe` : transcription complète minutée (`out/transcript.txt`) pour choisir `start`/`end`.
- `--preview` : images de contrôle `out/prev_clip_*.jpg`, `out/prev_end.jpg`, `out/cover.jpg` ; relire `out/subtitles.txt` et corriger les mots mal compris avec `fix`.
- Sans option : `out/video.mp4` (vignette 1 s + extrait habillé + carton de fin 2,8 s), `cover.jpg`, `post.txt`.
- `headline` : 2 lignes de 18 caractères max ; `role` : 45 caractères max ; `source` : 35 caractères max.
- Vidéo verticale (téléphone, TikTok) : plein cadre automatiquement. Vidéo horizontale : bandeau central recadré (`zoom`) sur fond flou.

## Short BUZZ (`"type": "buzz"`)
- Dossier `episodes/AAAA-MM-JJ-buzz/`, scènes hook → screen → brief → cta, 20 à 40 s.
- `cover_title` : titre de la vignette (2 lignes de 14 caractères max).
- `shot` : chemin relatif au dossier de l'épisode (ex. `shots/01.png`), produit par
  `python3 tools/capture.py URL <dossier>/shots/01.png --above 10 --height 220` (ajuster pour garder le titre, la date et le nom du média, sans pub ni pop-up).
  Les captures ne sont pas versionnées (`episodes/*/shots/` dans .gitignore).
- `source` : « Média ou @compte · JJ/MM/AAAA » (35 caractères max), affiché en très petit en haut à droite (« Photo : … ») ; à omettre pour une photo Unsplash.

## Short CULTURE (`"type": "culture"`, une actu)
- Champs de vignette : `"cover_style": "short"`, `"cover_pill": "CULTURE"`, `"cover_pill_color": "green"`, `"cover_title"` (2 lignes de 14 caractères max), `"cover_image_scene"` (index de la scène dont la photo sert de fond), `"cover_shot_scene"` (index de la scène screen dont la photo est mise en avant, ex. celle de l'artiste).
- `shot` d'une scène `screen` : photo de l'article téléchargée dans `shots/` (hors dépôt) ou capture (`tools/capture.py`). `image` peut aussi être un chemin local relatif au dossier.
- `credit` (facultatif, toute scène) : petite mention en haut à droite quand la photo de fond vient d'un média.

## Rendu 4K et luminosité
- Sortie 2160×3840 (vidéo et vignette). La mise en page reste en coordonnées 1080×1920 ; les fonds sont traités en 4K.
- `RENDER_SCALE=1 python3 pipeline/make.py …` pour un aperçu rapide en 1080p.
- Les URL Unsplash sont demandées automatiquement en `w=2400`. Les photos d'articles sont souvent en 960 à 1200 px : elles sont agrandies, donc on les montre plutôt cadrées (scène `screen`) qu'en plein écran.

## Règles de mise en page
- Titres : 2 lignes de 14 caractères max (3 lignes de 10 max pour civic).
- `stat` : 12 caractères max.
- Voix brief : 40 à 60 mots par info. Voix : fr-FR-HenriNeural, débit +5 %, timbre de Stéphane via `voice_ref` (assets/voix/stephane_se.json, hors dépôt).
- cover : titre court en MAJUSCULES pour la vignette TikTok (32 caractères max, ex. « RACKET ROUTIER : TOLÉRANCE ZÉRO »).
- problem / clear : 70 caractères max ; titres brief : 2 lignes de 18 caractères max.
- split accepte left_color et right_color (red, green, blue, yellow).
- Écrire les sigles comme ils se prononcent dans `voice` (« F M I », « CCC moins ») et normalement à l'écran.
