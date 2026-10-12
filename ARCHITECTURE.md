# Architecture de SataniawaBot

Le bot compte sept commandes principales actives. Les Cogs
regroupent les commandes Discord par fonctionnalité, les services gèrent les API,
et la configuration est chargée explicitement au démarrage.

```text
sataniawabot/
├── sataniawabot.py         # Point d’entrée : charger la configuration et lancer le bot
├── bot.py                 # Création du bot, intents, chargement des Cogs et erreurs
├── config.py              # Configuration, chemins et validation des clés
├── cogs/
│   ├── help.py            # Aide construite à partir des docstrings des commandes
│   ├── translation.py     # Commandes jp et ko
│   ├── music.py           # Commande music et liste des playlists
│   ├── valheim.py         # Groupe valheim et état du serveur local
│   └── fun.py             # Commandes sushi et anime ; avis lorsqu’elle sera activée
├── services/
│   ├── deepl.py           # Traduction et gestion des erreurs DeepL
│   ├── valheim.py         # Processus SteamCMD et compteur de joueurs via la console screen
│   └── spotify.py         # Récupération des titres et choix aléatoire
├── data/
│   ├── animes.json
│   └── avis.json
├── images/sushis/
├── requirements.txt
└── README.md              # Installation, configuration et lancement
```

## Responsabilités

- Les commandes valident les arguments et construisent les réponses Discord.
  Elles reçoivent les services nécessaires via le constructeur de leur Cog.
- Les services renvoient des données ou lèvent des exceptions explicites.
  Ils ne connaissent ni `ctx` ni les messages Discord. Le gestionnaire commun
  dans `bot.py` traduit leurs erreurs en messages lisibles pour l’utilisateur.
- `config.py` centralise les clés, les playlists et les chemins. Les secrets
  viennent de variables d’environnement, avec éventuellement `token.txt` comme
  solution de compatibilité. Aucune lecture de secret lors d’un simple import.
- `bot.py` charge les Cogs dans `setup_hook` et centralise les erreurs de commande
  (argument manquant, commande inconnue, API indisponible).
- Le point d’entrée utilise une fonction `main()` et une garde
  `if __name__ == "__main__":` pour permettre les imports sans connexion Discord.
- Chaque commande conserve une docstring courte avec sa fonction, sa syntaxe et
  éventuellement un exemple : l’aide reste synchronisée avec les commandes.

## Améliorations appliquées

1. Les chemins sont résolus depuis `Path(__file__).resolve().parent`, indépendamment
   du répertoire de lancement.
2. DeepL utilise une session HTTP asynchrone fermée à l’arrêt du bot. Spotipy
   s’exécute via `asyncio.to_thread`, avec un verrou pour son client synchrone.
   Les requêtes réseau ont un délai de dix secondes.
3. Spotify parcourt toutes les pages avant le tirage et exclut les titres absents,
   locaux ou sans nom, artiste ou lien exploitable. Son cache de token reste en mémoire.
4. Les journaux utilisent `logging`, sans réponses HTTP complètes ni texte traduit.
   La configuration DeepL est vérifiée avant tout appel réseau.
5. Les anciennes ébauches de commandes sont suivies dans `BACKLOG.md`.
6. `requirements.txt` déclare toutes les dépendances utilisées ; `README.md`
   documente les clés facultatives et le lancement réel de `sataniawabot.py`.

## Ordre de migration appliqué

La configuration et le point d’entrée ont été extraits, puis les services et les
Cogs (traduction, musique, divertissement). L’aide et les erreurs sont centralisées.
Les noms de commandes et le préfixe `>` sont conservés.

Les tests vérifient les cas utiles de cette migration : clés absentes, argument de
traduction manquant, playlist inconnue ou vide, titre Spotify absent, dossier
d’images vide et lancement depuis un autre répertoire. Les tests des services
peuvent simuler les API sans connexion Discord ni clés réelles.

Cette structure est implémentée. Les fonctionnalités non actives sont suivies
dans BACKLOG.md. Les vérifications automatisées se trouvent dans tests/.
