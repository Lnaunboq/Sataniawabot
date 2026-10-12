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

Les variables sont lues au lancement ; aucun fichier `.env` n’est chargé automatiquement.

| Variable | Usage |
| --- | --- |
| `DISCORD_TOKEN` | Token Discord obligatoire ; à défaut, fichier `token.txt` à côté du script |
| `DEEPL_API_KEY` | Facultative : traduction japonais/coréen ; endpoint Free pour les clés finissant par `:fx`, Pro sinon |
| `SPOTIFY_CLIENT_ID` | Facultative : à fournir avec le secret Spotify |
| `SPOTIFY_CLIENT_SECRET` | Facultative : à fournir avec l’identifiant Spotify |

Une paire Spotify incomplète produit une erreur de configuration au démarrage.
Sans clés API, le bot fonctionne et explique que le service demandé n’est pas
configuré. `>music list` reste disponible. Les playlists sont définies dans `config.py`.
Ne pas versionner les tokens et secrets.

## Lancement

Depuis le dossier `sataniawabot`, après avoir défini les variables souhaitées :

```sh
venv/bin/python sataniawabot.py
```

Depuis un autre dossier, utiliser les chemins absolus vers le Python du venv et
le script. Les images, données et `token.txt` sont résolus depuis le dossier du
bot. Depuis la racine du dépôt, le lancement en module fonctionne aussi :

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
| `>sushi` | Image aléatoire de `images/sushis/` |
| `>music [playlist]` | Titre aléatoire parmi tous les titres exploitables de la playlist ; `default` par défaut |
| `>music list` | Liste des playlists : default, weeb, sussy, rock |
| `>anime` | Répond actuellement « anime » ; fonctionnalité à développer |

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
