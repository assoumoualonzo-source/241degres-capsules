# Instructions des tâches planifiées

## INFO (tous les jours : lancement 17 h, capsule prête à 18 h, diffusion 19 h, heure de Libreville)
1. Cloner le dépôt, lire `docs/charte-editoriale.md` et `docs/episode-schema.md`.
2. Veille sur toutes les sources de la charte : 5 infos dont une sur le chef de l'État, à une place qui varie (jamais la même que la veille, jamais n°1 deux jours de suite), chacune confirmée par deux médias.
3. Pour chaque sujet : intérêt pour la population, intérêt pour l'État, réflexe citoyen.
4. Images selon les « Principes communs » de la charte : pertinence (on montre la personne, le lieu ou l'objet dont on parle), photos d'articles dans `shots/` (`"image": "shots/NN.jpg"` et `"credit": "Photo : Média · JJ/MM/AAAA"`), sinon Unsplash lumineux et lié au sujet (w=2400). Rendu 4K automatique.
5. Écrire `episodes/AAAA-MM-JJ-info/episode.json` (hook, 5 scènes brief, civic, cta ; voix clonée via voice_ref).
6. `python3 pipeline/make.py <dossier> --preview` : contrôler les images et la vignette out/cover.jpg (date, logo, 5 infos lisibles, rien de coupé ; champ `cover` de chaque brief), corriger, puis rendu final.
7. Envoyer `video.mp4`, `cover.jpg` et le texte de `post.txt` à l'utilisateur. Commit et push du JSON et de `post.txt`.

## VEILLE VIDÉOS (tous les jours, ~8 h 40 Libreville)
1. Veille sur les vidéos des dernières 24–48 h (section « Veille vidéos » de la charte).
2. Envoyer à Stéphane 3 à 5 vidéos classées : qui, quoi, lien, date, pourquoi elle fait parler (preuves), passage et minutage proposés, titre proposé, et un rappel du dossier Drive où déposer les extraits.
3. Rien à commit.

## EXTRAITS (tous les jours, ~12 h 40 et ~17 h 10 Libreville)
1. Lister les vidéos du dossier Drive « 241degres - Clips à traiter » (id 1_0fo_fZl7uTtcyscLEZeE_CmIefK87pO) qui n'ont pas encore de dossier `episodes/*-clip-*` avec le même `video_url`.
2. Pour chacune : `clip.json`, `--transcribe` si pas de minutage, choix du passage (20–45 s, phrase entière), `--preview`, contrôle des images et des sous-titres, rendu final.
3. Envoyer vidéo, vignette, légende. Commit et push de `clip.json` et `out/post.txt` uniquement.
4. Aucun fichier nouveau : ne rien envoyer.

## CULTURE (tous les jours, ~11 h 10 Libreville)
Un short sur une seule actu culturelle (section « Short CULTURE quotidien » de la charte), dossier `episodes/AAAA-MM-JJ-culture/`, modèle `episodes/2026-11-27-culture/episode.json`. Ne pas reprendre un sujet déjà traité dans les 7 derniers jours (regarder les dossiers `*-culture`). Photos d'articles dans `shots/` avec la source à l'écran. Rendu 4K. Envoyer vidéo, vignette, légende ; commit et push de `episode.json` et `out/post.txt`.
