# Charte éditoriale — @241degres

## Calendrier
- **Tous les jours** : une capsule INFO de 5 infos (90–110 s), prête à 18 h, diffusée à 19 h (heure de Libreville).
- **Un jour sur deux** : une capsule CULTURE (45–75 s) en plus.
- **Tous les matins** : la VEILLE VIDÉOS, liste des vidéos de personnalités publiques qui font parler (discours, entretiens, déclarations), envoyée à Stéphane.
- **Dès que Stéphane dépose un extrait** dans le dossier Drive « 241degres - Clips à traiter » : un short EXTRAIT (20–60 s).

## Public
Le Gabonais moyen, pas un spécialiste. Si un élève de 3e ne comprend pas une phrase, on la réécrit.

## Capsule INFO — structure
1. **hook** : étiquette « ACTU GABON », titre à l'écran « LES INFOS DU JOUR », voix : « Les infos du jour au Gabon. On t'explique. » (jamais « 5 infos chaudes » ni « en simple »).
2. **5 scènes brief**, une par info : titre + carte POURQUOI ÇA COMPTE (rouge) + carte CONCRÈTEMENT (vert). Les étiquettes restent à l'écran mais ne sont pas lues : la voix raconte l'info sans dire « Pourquoi ça compte » ni « Concrètement ».
   - **Info n°1 obligatoire : le chef de l'État** (activités, décisions, audiences, déplacements du président de la République). Ton factuel et neutre : ce qu'il a fait ou décidé, ce que ça change pour les gens. Pas d'éloge ni de critique de notre part.
   - Infos 2 à 5 : les plus « chaudes » des dernières 24 à 48 h (celles dont tout le monde parle, qui touchent le quotidien).
3. **civic** : un réflexe citoyen concret, lié à une des infos.
4. **cta** : « Abonne-toi pour recevoir nos capsules d'informations chaque jour ! Et dis-nous en commentaire ce que tu penses de ces actualités. »

## Veille vidéos et shorts EXTRAIT — discours, entretiens, déclarations
**Veille (chaque matin)** : les vidéos des dernières 24–48 h où un acteur politique ou une personnalité publique gabonaise (président, ministres, opposants, députés, syndicalistes, dirigeants, sportifs, artistes) dit quelque chose qui fait réagir. Sources : Gabon 24, Gabon 1ère, chaînes YouTube et pages des médias gabonais, RFI, France 24, TV5, Jeune Afrique, pages officielles, et les vidéos dont les médias parlent. Pour chaque vidéo : qui, quoi, où (lien), date, pourquoi elle fait parler (reprises dans les médias, vues si elles sont affichées), le passage à extraire avec son minutage s'il est connu, et un titre proposé. On ne présente jamais une estimation de vues comme un chiffre vérifié.
**Extraction** : Stéphane télécharge ou filme l'extrait et le dépose dans le dossier Drive « 241degres - Clips à traiter » (partagé « tous les utilisateurs disposant du lien »), nommé `AAAA-MM-JJ Nom - Média.mp4`. Il peut ajouter dans la description du fichier, ou dans un fichier texte du même nom, le lien d'origine et le minutage voulu.
**Le short EXTRAIT** (`pipeline/clip.py`) :
- Image et son d'origine, sans coupe qui change le sens : on garde la phrase entière et son contexte. Jamais de montage qui fait dire à quelqu'un ce qu'il n'a pas dit.
- Habillage : étiquette (DISCOURS, ENTRETIEN, DÉCLARATION, DÉBAT), titre = la phrase forte entre guillemets, telle qu'elle est prononcée ; nom et fonction de la personne ; sous-titres mot à mot ; « SOURCE : média · date » à l'écran du début à la fin ; vignette d'ouverture (1 s) et carton de fin (question + abonnement).
- 20 à 45 s conseillé, 60 s maximum : on cite un passage, on ne republie pas l'émission.
- Légende : contexte en une ou deux phrases neutres, la source et le lien de la vidéo d'origine.
- Équilibre : on ne suit pas un camp. Sur la durée, les extraits donnent la parole à la majorité, à l'opposition et à la société civile. Pas de commentaire moqueur ni d'emoji qui juge la personne.
- Interdits : particuliers filmés à leur insu, mineurs, propos haineux relayés sans recul, vidéos manipulées ou dont l'authenticité est douteuse (dans le doute, on écarte et on le signale à Stéphane), affaires judiciaires sans décision.
- Droits : courte citation à but d'information, source toujours citée. Si un média ou un auteur demande le retrait, on retire.

## Short BUZZ (format capture d'écran, à la demande)
Un seul sujet, celui dont tout le monde parle au Gabon depuis 24 h : annonce qui touche le quotidien, publication virale, polémique, exploit, rumeur à vérifier.
1. **hook** : étiquette « ÇA BUZZE », titre choc en question ou en constat (3 lignes de 10 caractères max), voix de 10 à 15 mots.
2. **screen** : la capture d'écran de la publication d'origine, avec l'étiquette « SOURCE : MÉDIA OU COMPTE · DATE » à l'écran. La voix dit ce qui est publié ou annoncé (25 à 35 mots).
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
2. **Place réservée** : info n°1 = chef de l'État.
3. **Classement des autres** : impact au quotidien (portefeuille, santé, sécurité, logement, démarches) > nombre de personnes concernées > chaleur (reprise par plusieurs médias, débat sur les réseaux) > échéance proche > équilibre des thèmes (5 thèmes différents).

## Veille et vérification
- Ratisser large chaque jour : L'Union (union.sonapresse.com), Gabon Media Time, Gabonreview, Info241, Gabonactu, Infos Gabon, AGP Gabon, Gabon 24, Direct Infos Gabon, allAfrica (Gabon), communiqués officiels (présidence, gouvernement).
- Pour l'info du chef de l'État : communiqués de la présidence et Gabon 24 en priorité.
- Chaque info doit être confirmée par **deux médias différents** ou une source officielle. Sinon, on l'écarte.
- Aucun chiffre de mémoire. Les sources (deux par info) vont dans `post.txt`.
- Pas d'affaires impliquant des mineurs, pas de rumeurs, pas de faits divers sordides.

## Capsule CULTURE — formats en rotation
- Top 10 des plus belles villes ou des plus beaux sites (Libreville, Port-Gentil, Lambaréné, Franceville, Oyem, Lopé, Loango, Pongara, Akanda, Kongou…).
- Top 5 ou 10 des artistes gabonais qui montent sur YouTube et TikTok (classement par abonnés ou vues **vérifiés le jour même**).
- « Le saviez-vous ? » : histoire, langues (fang, punu, myènè, nzebi…), traditions (Bwiti, masques punu), gastronomie (nyembwe, odika, manioc).
- Portrait express : une figure gabonaise inspirante (sport, sciences, entrepreneuriat).
- Montage « carte postale » d'une ville : 5 raisons d'y aller.
- Nature : parcs nationaux, faune (éléphants de forêt, baleines à Mayumba, tortues luths).

## Règles images et droits
- Photos libres de droit uniquement (Unsplash, Pexels, Wikimedia Commons en CC). Les crédits vont dans `post.txt`.
- Jamais de clips, pochettes ou photos d'artistes protégés : on cite leurs noms et leurs chiffres, et le visuel reste générique (ville, scène, instruments).
- Musique générée par le pipeline (libre de droits). Sur TikTok, on peut remplacer la piste par un son tendance de la bibliothèque commerciale de TikTok.
