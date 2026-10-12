class ServiceError(Exception):
    """Erreur présentable à l’utilisateur, sans contenu sensible."""


class NotConfigured(ServiceError):
    """Service sans identifiants configurés."""


class EmptyPlaylist(ServiceError):
    """Playlist sans titre exploitable."""
