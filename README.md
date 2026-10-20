# SataniawaBot

Bot Discord utilisant le préfixe `>`. Les commandes sont regroupées dans `cogs/`,
les intégrations API dans `services/` et la configuration dans `config.py`.
Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour les responsabilités de chaque module.

## Installation

Python 3.10 ou ultérieur. Depuis le dossier `sataniawabot` :

```sh
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Activer **Message Content Intent** dans le portail développeur Discord pour le bot.

## Configuration

Les clés API sont lues au lancement dans `clés.txt` ou `clé.txt`, à côté de
`sataniawabot.py`. Si les deux existent, `clé.txt` est prioritaire. Les variables
d’environnement sont prioritaires sur ces fichiers, même lorsqu’elles sont vides.
Aucun fichier `.env` n’est chargé automatiquement.

| Variable | Usage |
| --- | --- |
| `DISCORD_TOKEN` | Token Discord obligatoire ; à défaut, fichier `token.txt` à côté du script |
| `DEEPL_API_KEY` | Facultative : traduction japonais/coréen ; endpoint Free pour les clés finissant par `:fx`, Pro sinon |
| `SPOTIFY_CLIENT_ID` | Facultative : à fournir avec le secret Spotify |
| `SPOTIFY_CLIENT_SECRET` | Facultative : à fournir avec l’identifiant Spotify |
| `VALHEIM_SERVER_NAME` | Nom exact passé à `-name` dans le lancement SteamCMD ; `Serveur Gangserv3` par défaut |
| `VALHEIM_SCREEN_NAME` | Session screen contenant la console du serveur en fenêtre 0 ; `Gangserv3` par défaut |

Une paire Spotify incomplète produit une erreur de configuration au démarrage.
Sans clés API, le bot fonctionne et explique que le service demandé n’est pas
configuré. `>music list` reste disponible. Les playlists sont définies dans `config.py`.
Ne pas versionner les tokens et secrets.

## Rebrancher DeepL et Spotify

Créer ou remplir `clé.txt` (ou `clés.txt`) à côté de `sataniawabot.py` :

```sh
DEEPL_API_KEY='ta-cle-deepl'
SPOTIFY_CLIENT_ID='ton-client-id'
SPOTIFY_CLIENT_SECRET='ton-client-secret'
```

Ces deux noms de fichier sont ignorés par Git. Les guillemets sont retirés à la
lecture ; aucune commande shell n’est exécutée. Les lignes vides et les commentaires
`#` sont acceptés. Le token Discord peut rester dans `token.txt`.

Redémarrer le bot après toute modification : les fichiers sont lus automatiquement,
sans `source` ni export, quel que soit le répertoire de lancement. Un simple
`python3 sataniawabot.py` depuis le dossier du bot suffit (ou le Python du venv).

### DeepL

Récupérer une clé dans [le compte DeepL, rubrique clés API](https://www.deepl.com/your-account/keys)
et la placer dans `DEEPL_API_KEY` dans ton fichier de clés. Il faut un abonnement **DeepL API** ; un abonnement
au traducteur seul ne fournit pas forcément de clé.
Voir [l’aide officielle sur les clés](https://support.deepl.com/hc/en-us/articles/360020695820-API-key-for-DeepL-API).
Le code sélectionne déjà le serveur Free ou Pro selon la clé.
Après redémarrage, essayer `>jp Bonjour` puis `>ko Bonjour`.
Une réponse HTTP 403 indique un refus d’authentification ou d’accès ; 456 indique
un quota dépassé, à vérifier dans le compte DeepL.

### Spotify

Retrouver l’application dans [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
et renseigner ensemble `SPOTIFY_CLIENT_ID` et `SPOTIFY_CLIENT_SECRET`.
**Cela ne garantit pas le fonctionnement de `>music` avec une application en mode
Development.** Le code actuel utilise Client Credentials, sans connexion utilisateur.

D’après le [guide officiel de migration 2026](https://developer.spotify.com/documentation/web-api/tutorials/february-2026-migration-guide),
le mode Development impose désormais Premium au propriétaire de l’application,
le nouvel endpoint `/playlists/{id}/items` et un accès limité au contenu des
playlists appartenant à l’utilisateur connecté ou dont il est collaborateur.
La playlist `default` actuelle appartient à Spotify : elle devra être remplacée
par une playlist accessible de ton compte dans `config.py`.

Pour ce mode, il reste donc une migration du code à faire : connexion utilisateur
OAuth Authorization Code avec URI de retour enregistrée dans le Dashboard,
conservation et renouvellement du jeton, permissions `playlist-read-private` et
`playlist-read-collaborative` selon les playlists, puis adaptation de l’endpoint
et du champ de réponse `track` devenu `item`. Les secrets seuls ne remplacent pas
cette autorisation. Voir [Authorization Code](https://developer.spotify.com/documentation/web-api/tutorials/code-flow).
Les applications en Extended Quota sont exemptées des changements décrits dans
ce guide ; leur intégration actuelle peut être essayée avec les deux identifiants.

`>music list` permet de vérifier la liste locale sans API. `>music rock` vérifie
ensuite l’accès réel, mais le message d’erreur actuel regroupe les refus d’accès
et les indisponibilités : il ne prouve pas à lui seul qu’une clé est incorrecte.

## Lancement

Depuis le dossier `sataniawabot`, après avoir défini les variables souhaitées :

```sh
venv/bin/python sataniawabot.py
```

Depuis un autre dossier, utiliser les chemins absolus vers le Python du venv et
le script. Les fichiers de configuration sont résolus depuis le dossier du bot. Depuis la racine du dépôt, le lancement en module fonctionne aussi :

```sh
sataniawabot/venv/bin/python -m sataniawabot.sataniawabot
```

Les journaux utilisent `logging`. Ils ne contiennent pas les textes traduits,
les réponses HTTP complètes ou les identifiants API.

## Commandes

| Commande | Fonction |
| --- | --- |
| `>help [commande]` | Liste des commandes ou aide détaillée |
| `>jp <texte>` | Traduction en japonais avec DeepL |
| `>ko <texte>` | Traduction en coréen avec DeepL |
| `>sushi` | Recherche une image de sushi sur TheMealDB et l’affiche dans le message |
| `>music [playlist]` | Titre aléatoire parmi tous les titres exploitables de la playlist ; `default` par défaut |
| `>music list` | Liste des playlists : default, weeb, sussy, rock |
| `>valheim` ou `>valheim status` | Indique si le processus du serveur Gangserv3 est lancé |
| `>valheim player` ou `>valheim players` | Dernier compteur de joueurs, heure de mesure et noms lorsqu’ils sont disponibles |

La vérification Valheim lit les processus locaux dans `/proc` sous Linux et fonctionne
avec un lancement dans `screen`. Le bot doit tourner sur la même machine et pouvoir
lire les processus Valheim. Le nom doit correspondre à l’argument `-name` du serveur,
pas au nom de la session screen ni au nom du monde. Un processus lancé est affiché
« allumé », même pendant le chargement du monde. Une erreur de lecture donne un
état indéterminé plutôt qu’un faux « éteint ».

La commande `player` copie temporairement le scrollback de la fenêtre 0 de screen,
puis lit la dernière ligne `Connections`. Le compteur est publié par Valheim environ
toutes les dix minutes : ce n’est pas une mesure instantanée. L’heure affichée est
celle du serveur. Les noms sont affichés seulement lorsque les événements du journal
permettent de reconstituer une liste correspondant au compteur. Le bot doit être lancé
avec le même utilisateur que la session screen et avoir accès à la commande `screen`.
La copie temporaire est supprimée après lecture ; aucun fichier de logs permanent
n’est activé. Une console inaccessible ou sans mesure produit une erreur explicite.

L’aide utilise les docstrings des commandes. Les erreurs d’arguments et de
services sont transformées en messages Discord par `bot.py`. Les mentions sont
désactivées dans les réponses pour éviter les notifications issues des textes.

## Vérifications

Depuis la racine du dépôt :

```sh
python3 -m unittest discover -s sataniawabot/tests -v
```

Ces tests n’utilisent ni clés réelles ni connexion Discord. Ils simulent les API,
vérifient les erreurs, les playlists paginées, l’aide et les chemins indépendants
du répertoire de lancement. Un essai sur Discord reste nécessaire pour vérifier
les permissions et les identifiants réels.

`>sushi` interroge [TheMealDB](https://www.themealdb.com/api.php) à chaque appel,
sans compte ni clé personnelle, avec la clé publique de test `1` autorisée pour
le développement et l’usage éducatif. Aucune image n’est stockée sur le serveur
ou dans le dépôt. Le service ne propose actuellement qu’une recette de sushi :
la même image peut donc revenir. Une publication sur un appstore nécessite un
abonnement selon la documentation TheMealDB.

Discord affiche l’image via son URL dans un embed avec un lien vers la recette ;
le bot doit avoir la permission **Intégrer des liens**. Une panne, un délai dépassé
ou une réponse invalide produit un message explicite. Aucun fichier local ne
sert de secours. `WIKIMEDIA_CONTACT` n’est plus nécessaire ; si cette ancienne
option est encore dans `clé.txt`, elle est ignorée. Redémarrer le bot après la mise à jour.
