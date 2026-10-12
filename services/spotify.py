"""Accès Spotify hors de la boucle Discord et tirage sur toute la playlist."""
import asyncio
import random
from dataclasses import dataclass
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from .errors import EmptyPlaylist, NotConfigured, ServiceError


@dataclass(frozen=True)
class Track:
    name: str
    artists: str
    url: str


class SpotifyService:
    def __init__(self, client=None):
        self.client = client
        self._lock = asyncio.Lock()

    @classmethod
    def from_config(cls, config):
        if not config.spotify_client_id or not config.spotify_client_secret:
            return cls()
        auth = SpotifyClientCredentials(
            client_id=config.spotify_client_id,
            client_secret=config.spotify_client_secret,
            cache_handler=spotipy.cache_handler.MemoryCacheHandler(),
            requests_timeout=10,
        )
        return cls(spotipy.Spotify(
            auth_manager=auth, requests_timeout=10, retries=0, status_retries=0,
        ))

    async def random_track(self, playlist_id):
        if self.client is None:
            raise NotConfigured("Spotify n’est pas configuré.")
        async with self._lock:
            try:
                return await asyncio.to_thread(self._random_track, playlist_id)
            except (spotipy.SpotifyException, spotipy.SpotifyOauthError, requests.RequestException):
                raise ServiceError("Spotify est indisponible ou la playlist est inaccessible.") from None
            except (KeyError, TypeError, ValueError):
                raise ServiceError("Spotify a renvoyé une réponse invalide.") from None

    def _random_track(self, playlist_id):
        page = self.client.playlist_items(playlist_id, additional_types=["track"], limit=100)
        tracks = []
        while page:
            for item in page.get("items", []):
                track = item.get("track") if isinstance(item, dict) else None
                if (
                    not isinstance(track, dict)
                    or track.get("is_local")
                    or track.get("type", "track") != "track"
                ):
                    continue
                name = track.get("name")
                urls = track.get("external_urls") or {}
                url = urls.get("spotify") if isinstance(urls, dict) else None
                artists = track.get("artists") or []
                names = [
                    artist["name"] for artist in artists
                    if isinstance(artist, dict)
                    and isinstance(artist.get("name"), str) and artist["name"]
                ]
                if (
                    isinstance(name, str) and name
                    and isinstance(url, str) and url and names
                ):
                    tracks.append(Track(name, ", ".join(names), url))
            page = self.client.next(page) if page.get("next") else None
        if not tracks:
            raise EmptyPlaylist("Aucun titre exploitable trouvé dans cette playlist.")
        return random.choice(tracks)
