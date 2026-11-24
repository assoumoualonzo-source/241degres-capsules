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
| brief | kicker, headline, problem, clear, cover | une info : titre + CE QUI COINCE + EN CLAIR (format INFO quotidien) |
| story | kicker, headline, stat, stat_label | une actu + un chiffre |
| split | kicker, left_title, left, right_title, right | pour vous / pour l'État |
| alert | kicker, headline, bullets[3] (les 2 premières = interdits, la dernière = action) | arnaque, sécurité |
| civic | kicker, headline (3 lignes courtes), question | réflexe citoyen + question |
| cta | kicker, headline, sub | abonnement + commentaires |
| rank | kicker, rank, headline, stat, stat_label | élément de top (culture) |

Chaque scène a `image` (URL d'une photo libre de droit, portrait de préférence) et `voice` (texte lu). La durée de la scène suit la voix.

## Règles de mise en page
- Titres : 2 lignes de 14 caractères max (3 lignes de 10 max pour civic).
- `stat` : 12 caractères max.
- Voix brief : 40 à 60 mots par info. Voix : fr-FR-HenriNeural, débit +5 %, timbre de Stéphane via `voice_ref` (assets/voix/stephane_se.json, hors dépôt).
- cover : titre court en MAJUSCULES pour la vignette TikTok (32 caractères max, ex. « RACKET ROUTIER : TOLÉRANCE ZÉRO »).
- problem / clear : 70 caractères max ; titres brief : 2 lignes de 18 caractères max.
- split accepte left_color et right_color (red, green, blue, yellow).
- Écrire les sigles comme ils se prononcent dans `voice` (« F M I », « CCC moins ») et normalement à l'écran.
