# Instructions des tâches planifiées

## INFO (tous les jours : lancement 17 h, capsule prête à 18 h, diffusion 19 h, heure de Libreville)
1. Cloner le dépôt, lire `docs/charte-editoriale.md` et `docs/episode-schema.md`.
2. Veille sur toutes les sources de la charte : 5 infos (n°1 = chef de l'État), chacune confirmée par deux médias.
3. Pour chaque sujet : intérêt pour la population, intérêt pour l'État, réflexe citoyen.
4. Images libres de droit (Unsplash) en orientation portrait.
5. Écrire `episodes/AAAA-MM-JJ-info/episode.json` (hook, 5 scènes brief, civic, cta ; voix clonée via voice_ref).
6. `python3 pipeline/make.py <dossier> --preview` : contrôler les images et la vignette out/cover.jpg (date, logo, 5 infos lisibles, rien de coupé ; champ `cover` de chaque brief), corriger, puis rendu final.
7. Envoyer `video.mp4`, `cover.jpg` et le texte de `post.txt` à l'utilisateur. Commit et push du JSON et de `post.txt`.

## BUZZ (tous les jours : lancement ~11 h 20, short prêt à 12 h 30, diffusion 13 h, heure de Libreville)
1. Cloner le dépôt, lire la section « Short BUZZ » de la charte et `docs/episode-schema.md`.
2. Veille sur l'actu chaude et les publications virales du Gabon des dernières 24 h (médias de la charte, pages officielles, tendances relayées par les médias). Choisir UN sujet, différent des 3 derniers dossiers `*-buzz` et, si possible, de la capsule INFO de la veille.
3. Vérifier : deux sources ou une source officielle. Rumeur non confirmée : on la traite en « VRAI OU FAUX ? », jamais comme un fait.
4. Capture de la publication d'origine avec `tools/capture.py`, la regarder et la recadrer si besoin.
5. Écrire `episodes/AAAA-MM-JJ-buzz/episode.json` (hook, screen, brief, cta ; voix clonée via voice_ref), preview, contrôle, rendu final.
6. Envoyer `video.mp4`, `cover.jpg`, `post.txt` et la légende (avec le lien de la publication d'origine). Commit et push du JSON et de `post.txt` uniquement.

## CULTURE (un jour sur deux, ~11 h 30 Libreville)
Même chaîne avec `episodes/AAAA-MM-JJ-culture/`. Format tiré de la rotation de la charte, différent des 3 derniers (regarder l'historique des dossiers `*-culture`). Pour un top : scènes `rank` du dernier au premier, hook « TOP 5 … », cta. Classements d'artistes vérifiés le jour même, aucun visuel protégé.
