# Fonctionnalités à terminer

Ces fonctionnalités existaient sous forme de code commenté ou de placeholder.
Elles ne sont pas chargées comme commandes supplémentaires.

- **Anime** : définir comment exploiter `data/animes.json` et le format de la
  réponse. La commande actuelle répond toujours « anime ».
- **Avis** : lire `data/avis.json`, choisir une phrase et envoyer
  `!donneavis sur <phrase>`. Prévoir un message lorsque les données sont absentes,
  invalides ou vides, puis ajouter la commande au Cog de divertissement.
- **Gestion des serveurs** : créer un Cog réservé au propriétaire du bot.
  L’ancienne ébauche prévoyait un menu de serveurs et un bouton pour quitter le
  serveur choisi. Prévoir pagination (limite des options Discord), contrôle de
  l’auteur des interactions, expiration de la vue, confirmation et erreurs de
  permissions avant activation.
