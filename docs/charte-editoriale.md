# Charte éditoriale — @241degres

## Calendrier
- **Tous les jours** : une capsule INFO de 5 infos (90–110 s), prête à 18 h, diffusée à 19 h (heure de Libreville).
- **Tous les jours** : un short CULTURE (30–45 s) sur **une seule** actu culturelle (depuis le 27/11/2026, remplace la capsule culture « un jour sur deux »).
- **Tous les matins** : la VEILLE VIDÉOS, liste des vidéos de personnalités publiques qui font parler (discours, entretiens, déclarations), envoyée à Stéphane.
- **Dès que Stéphane dépose un extrait** dans le dossier Drive « 241degres - Clips à traiter » : un short EXTRAIT (20–60 s).

## Principes communs à TOUTES les capsules (INFO, CULTURE, BUZZ, EXTRAIT) — depuis le 27/11/2026
Démarche d'amélioration continue (PDCA) : chaque retour de Stéphane devient une règle ici, pour tous les formats.
1. **Pertinence de l'image** : à chaque scène, l'image montre ce dont parle la voix (la personne, le lieu, l'objet, l'événement). Quand on parle de quelqu'un, on le montre. Une photo d'article qui ne montre pas le sujet (conférence de presse, tribune, logo) n'est pas utilisée. Une photo générique n'est qu'un dernier recours, et alors elle doit représenter le sujet (un chœur pour un concert de chœur, une pompe à essence pour le carburant).
2. **Photos d'articles** : autorisées et recherchées (og:image et photos du corps de l'article, téléchargées dans `shots/`, hors dépôt). Les questions de droits et de retrait sont gérées par Stéphane.
3. **Source** : pas de bandeau « SOURCE ». Seulement quand l'image (ou la vidéo, ou la capture) vient d'un média : « Photo : Média · date » (« Source : … » pour un extrait vidéo) en très petit en haut à droite, et en bas à droite sur la vignette. Rien pour une photo Unsplash. La source complète va dans la légende et `post.txt`.
4. **Vignette** : un sujet fort et lisible dans la grille du profil, avec l'image de la personne ou du sujet principal (champ `cover_shot_scene` pour les shorts ; pour la capsule INFO, l'image de l'info n°1, quelle qu'elle soit, doit être parlante et lumineuse).
5. **4K et luminosité** : vidéo et vignette en 2160×3840 ; fonds lumineux, voiles légers ; photos Unsplash en grande taille (w=2400).
6. **Lisibilité** : rien ne chevauche les sous-titres ni le texte ; vérifier les images de contrôle avant chaque rendu final.
7. **Prononciation** (champ `voice`) : Mayumba = « Mayoumba » ; Ivindo, « in » comme dans « cuisine » ; sigles écrits comme ils se prononcent.

## Public
Le Gabonais moyen, pas un spécialiste. Si un élève de 3e ne comprend pas une phrase, on la réécrit.

## Capsule INFO — structure
1. **hook** : étiquette « ACTU GABON », titre à l'écran « LES INFOS DU JOUR », voix : « Les infos du jour au Gabon. On t'explique. » (jamais « 5 infos chaudes » ni « en simple »).
2. **5 scènes brief**, une par info : titre + carte POURQUOI ÇA COMPTE (rouge) + carte CONCRÈTEMENT (vert). Les étiquettes restent à l'écran mais ne sont pas lues : la voix raconte l'info sans dire « Pourquoi ça compte » ni « Concrètement ».
   - **Une info sur le chef de l'État chaque jour, à une place qui varie** (depuis le 28/11/2026) : activités, décisions, audiences, déplacements du président de la République. Ton factuel et neutre : ce qu'il a fait ou décidé, ce que ça change pour les gens. Pas d'éloge ni de critique de notre part. Pour ne pas donner l'image d'un média partisan, elle n'est **pas** systématiquement en premier (voir « Sélection des 5 infos »).
   - Les autres infos : les plus « chaudes » des dernières 24 à 48 h (celles dont tout le monde parle, qui touchent le quotidien).
   - Étiquette (`kicker`) et voix par thème, pas par personne : « 3 · INDUSTRIE », « Troisième info, l'industrie », plutôt que « CHEF DE L'ÉTAT » ou « Première info, le chef de l'État ».
3. **civic** : un réflexe citoyen concret, lié à une des infos.
4. **cta** : « Abonne-toi pour recevoir nos capsules d'informations chaque jour ! Et dis-nous en commentaire ce que tu penses de ces actualités. »

## Veille vidéos et shorts EXTRAIT — discours, entretiens, déclarations
**Veille (chaque matin)** : les vidéos des dernières 24–48 h où un acteur politique ou une personnalité publique gabonaise (président, ministres, opposants, députés, syndicalistes, dirigeants, sportifs, artistes) dit quelque chose qui fait réagir. Sources : Gabon 24, Gabon 1ère, chaînes YouTube et pages des médias gabonais, RFI, France 24, TV5, Jeune Afrique, pages officielles, et les vidéos dont les médias parlent. Pour chaque vidéo : qui, quoi, où (lien), date, pourquoi elle fait parler (reprises dans les médias, vues si elles sont affichées), le passage à extraire avec son minutage s'il est connu, et un titre proposé. On ne présente jamais une estimation de vues comme un chiffre vérifié.
**Extraction** : Stéphane télécharge ou filme l'extrait et le dépose dans le dossier Drive « 241degres - Clips à traiter » (partagé « tous les utilisateurs disposant du lien »), nommé `AAAA-MM-JJ Nom - Média.mp4`. Il peut ajouter dans la description du fichier, ou dans un fichier texte du même nom, le lien d'origine et le minutage voulu.
**Le short EXTRAIT** (`pipeline/clip.py`) :
- Image et son d'origine, sans coupe qui change le sens : on garde la phrase entière et son contexte. Jamais de montage qui fait dire à quelqu'un ce qu'il n'a pas dit.
- Habillage : étiquette (DISCOURS, ENTRETIEN, DÉCLARATION, DÉBAT), titre = la phrase forte entre guillemets, telle qu'elle est prononcée ; nom et fonction de la personne ; sous-titres mot à mot ; « Source : média · date » en très petit en haut à droite du début à la fin ; vignette d'ouverture (1 s) et carton de fin (question + abonnement).
- 20 à 45 s conseillé, 60 s maximum : on cite un passage, on ne republie pas l'émission.
- Légende : contexte en une ou deux phrases neutres, la source et le lien de la vidéo d'origine.
- Équilibre : on ne suit pas un camp. Sur la durée, les extraits donnent la parole à la majorité, à l'opposition et à la société civile. Pas de commentaire moqueur ni d'emoji qui juge la personne.
- Interdits : particuliers filmés à leur insu, mineurs, propos haineux relayés sans recul, vidéos manipulées ou dont l'authenticité est douteuse (dans le doute, on écarte et on le signale à Stéphane), affaires judiciaires sans décision.
- Droits : courte citation à but d'information, source toujours citée. Si un média ou un auteur demande le retrait, on retire.

## Short BUZZ (format capture d'écran, à la demande)
Un seul sujet, celui dont tout le monde parle au Gabon depuis 24 h : annonce qui touche le quotidien, publication virale, polémique, exploit, rumeur à vérifier.
1. **hook** : étiquette « ÇA BUZZE », titre choc en question ou en constat (3 lignes de 10 caractères max), voix de 10 à 15 mots.
2. **screen** : la capture d'écran de la publication d'origine, avec « Photo : média ou compte · date » en très petit en haut à droite. La voix dit ce qui est publié ou annoncé (25 à 35 mots).
3. **brief** : « VRAI OU FAUX ? » / « CE QU'ON SAIT VRAIMENT » : ce qui est confirmé, ce qui ne l'est pas, ce que ça change pour toi (25 à 35 mots).
4. **cta** court : « Et toi, tu en penses quoi ? Dis-le en commentaire, et abonne-toi pour ne rien rater ! »
- Vignette : grand titre (`cover_title`), pastille ÇA BUZZE, la capture et sa source.
- Vérification : le buzz est confirmé par **deux sources** (dont la publication d'origine) ou par une source officielle. Si c'est une rumeur, on le dit clairement (« FAUX » ou « PAS CONFIRMÉ ») : on ne relaie jamais une rumeur comme un fait.
- Captures d'écran (`tools/capture.py`) : uniquement des publications de **médias, d'institutions, de personnalités publiques ou d'entreprises** (articles, communiqués, posts publics). Jamais la publication d'un particulier, jamais un mineur, jamais de contenu choquant. Le nom du média ou du compte et la date sont **toujours** à l'écran et dans la légende.
- On ne retélécharge jamais la vidéo d'un autre compte. Pour une vidéo virale, on montre une capture créditée du post et on donne son lien dans la légende ; Stéphane peut aussi faire un Stitch ou un Duo TikTok, qui crédite l'auteur automatiquement.
- Mêmes interdits que la capsule INFO : pas de fait divers sordide, pas d'affaire judiciaire sans décision, pas d'attaque contre une personne.

## Ton
- Tutoiement, phrases de moins de 15 mots, vocabulaire de la rue et du marché.
- Zéro jargon : pas de « PIB », « déficit », « notation souveraine », « réforme structurelle ». On traduit : « l'argent de l'État », « les dettes », « la note du pays ».
- Comparaisons du quotidien (« Fitch note les pays comme on note les élèves »).
- Au maximum un chiffre par info, et seulement s'il parle à tout le monde.
- Approche civique, jamais partisane : ce que ça change pour les gens, ce que fait l'État, ce que chacun peut faire. Pas d'opinion sur des personnes ni sur des partis.

## Choix des sujets (par ordre de priorité)
1. Ce qui touche le portefeuille, la santé, la sécurité ou les démarches des Gabonais.
2. Les décisions publiques avec une échéance (dates limites, réformes, budgets).
3. Les bonnes nouvelles vérifiables (investissements, infrastructures, réussites).
On évite : faits divers sordides, rumeurs, sujets judiciaires en cours sans décision.

## Sélection des 5 infos
1. **Filtres éliminatoires** : vérifiée (deux médias différents ou source officielle), fraîche (24–48 h ou fait nouveau), sûre (pas de rumeur, pas de fait divers sordide, pas de mineurs, pas d'affaire judiciaire sans décision).
2. **Info du chef de l'État** : toujours présente, mais classée comme les autres selon les critères ci-dessous, donc à une place qui change d'un jour à l'autre. Règles d'alternance : jamais à la même place deux jours de suite (regarder la capsule de la veille dans `episodes/*-info`), jamais en n°1 deux jours de suite, et au plus deux fois en n°1 sur sept jours. En n°1 seulement si c'est vraiment l'info qui touche le plus le quotidien des gens ce jour-là.
3. **Classement** : impact au quotidien (portefeuille, santé, sécurité, logement, démarches) > nombre de personnes concernées > chaleur (reprise par plusieurs médias, débat sur les réseaux) > échéance proche > équilibre des thèmes (5 thèmes différents).

## Veille et vérification
- Ratisser large chaque jour : L'Union (union.sonapresse.com), Gabon Media Time, Gabonreview, Info241, Gabonactu, Infos Gabon, AGP Gabon, Gabon 24, Direct Infos Gabon, allAfrica (Gabon), communiqués officiels (présidence, gouvernement).
- Pour l'info du chef de l'État : communiqués de la présidence et Gabon 24 en priorité.
- Chaque info doit être confirmée par **deux médias différents** ou une source officielle. Sinon, on l'écarte.
- Aucun chiffre de mémoire. Les sources (deux par info) vont dans `post.txt`.
- Pas d'affaires impliquant des mineurs, pas de rumeurs, pas de faits divers sordides.

## Short CULTURE quotidien (une actu à la fois)
Modèle : `episodes/2026-11-27-culture/episode.json` (inspiré du short BUZZ).
- **Sujet** : une actu culturelle gabonaise fraîche (24–72 h) ou un événement des jours qui viennent : concert, festival, expo, film, livre, mode, prix gagné par un Gabonais, patrimoine. Priorité à ce qui se passe « ce soir / ce week-end » avec date, lieu et prix.
- **Structure** : hook (étiquette CULTURE, 3 lignes de 10 caractères max) → 1 ou 2 scènes `screen` avec la photo de l'article ou une capture, et la source à l'écran → `brief` PRATIQUE (date, lieu, prix) → cta « Tu y vas ? / Ton avis en commentaire ».
- **Vignette** : style short (`cover_style: "short"`, pastille verte CULTURE, gros titre, photo de l'article et sa source).
- **Vérification** : faits et chiffres lus le jour même dans l'article ; deux médias de préférence. Si une seule source (annonce d'organisateur relayée par un média), le signaler à Stéphane. Si l'orthographe d'un nom ou d'un titre diffère entre deux sources, on ne l'écrit pas.
- **Photos d'articles** : autorisées et recherchées quand elles montrent le sujet (l'artiste, l'œuvre, le lieu). Source indiquée dans la légende. Les questions de droits et de retrait sont gérées par Stéphane.
- **Pertinence** : à chaque scène, l'image montre ce dont parle la voix (un chœur quand on parle d'un concert de chœur, l'artiste quand on parle de l'artiste). Une photo d'article qui ne montre pas le sujet (conférence de presse, tribune officielle, logo) n'est pas utilisée. Quand on parle d'un artiste, on montre l'artiste (photo de l'article) et on la met sur la vignette (`cover_shot_scene`).
- **Source à l'écran** : pas de bandeau. Seulement pour une image de média : « Photo : Média · date » en très petit en haut à droite (et en bas à droite sur la vignette). Rien pour une photo Unsplash.
- **Image** : rendu 4K (2160×3840), fonds lumineux (pas de voile sombre), photos d'ambiance Unsplash demandées en grande taille.
- **Prononciation** (champ `voice`) : Mayumba se dit « Mayoumba » ; Ivindo, « in » comme dans « cuisine ».

## Capsule CULTURE — anciens formats (réservés à un sujet de fond, sur demande)
- Top 10 des plus belles villes ou des plus beaux sites (Libreville, Port-Gentil, Lambaréné, Franceville, Oyem, Lopé, Loango, Pongara, Akanda, Kongou…).
- Top 5 ou 10 des artistes gabonais qui montent sur YouTube et TikTok (classement par abonnés ou vues **vérifiés le jour même**).
- « Le saviez-vous ? » : histoire, langues (fang, punu, myènè, nzebi…), traditions (Bwiti, masques punu), gastronomie (nyembwe, odika, manioc).
- Portrait express : une figure gabonaise inspirante (sport, sciences, entrepreneuriat).
- Montage « carte postale » d'une ville : 5 raisons d'y aller.
- Nature : parcs nationaux, faune (éléphants de forêt, baleines à Mayumba, tortues luths).

## Règles images et droits
- Voir « Principes communs » : photos d'articles et d'institutions recherchées quand elles montrent le sujet, sinon photos libres (Unsplash, Pexels, Wikimedia Commons en CC) qui représentent le sujet. Les crédits vont dans `post.txt`.
- Jamais de clips, pochettes ou photos d'artistes protégés : on cite leurs noms et leurs chiffres, et le visuel reste générique (ville, scène, instruments).
- Musique générée par le pipeline (libre de droits). Sur TikTok, on peut remplacer la piste par un son tendance de la bibliothèque commerciale de TikTok.
