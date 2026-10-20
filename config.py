"""Configuration chargée explicitement au démarrage."""
import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

BASE_DIR = Path(__file__).resolve().parent
PLAYLISTS = {
    "default": "37i9dQZF1DXcBWIGoYBM5M",
    "weeb": "1slD6f3tiZLLCQXivuAotL",
    "sussy": "5A7t2KdFJb9oBeGECBf4Xp",
    "rock": "4uBqThgovepwPVCkbsO3lS",
}


@dataclass(frozen=True)
class Config:
    token: str = field(repr=False)
    deepl_api_key: str = field(default="", repr=False)
    spotify_client_id: str = field(default="", repr=False)
    spotify_client_secret: str = field(default="", repr=False)
    base_dir: Path = BASE_DIR
    playlists: Mapping[str, str] = field(default_factory=lambda: dict(PLAYLISTS))
    valheim_server_name: str = "Serveur Gangserv3"
    valheim_screen_name: str = "Gangserv3"


def _load_api_keys(base_dir):
    keys = {}
    allowed = {"DEEPL_API_KEY", "SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET"}
    for filename in ("clés.txt", "clé.txt"):
        path = base_dir / filename
        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except FileNotFoundError:
            continue
        for number, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, separator, value = line.partition("=")
            if not separator or name.strip() not in allowed:
                raise RuntimeError(f"Configuration invalide dans {filename}, ligne {number} : utiliser NOM='valeur' pour les clés API.")
            try:
                parts = shlex.split(value, comments=True)
                if len(parts) > 1:
                    raise ValueError()
            except ValueError:
                raise RuntimeError(f"Configuration invalide dans {filename}, ligne {number} : vérifier les guillemets.") from None
            keys[name.strip()] = parts[0] if parts else ""
    return keys


def load_config(environ=None, base_dir=BASE_DIR):
    base_dir = Path(base_dir).resolve()
    env = _load_api_keys(base_dir)
    env.update(os.environ if environ is None else environ)
    token = env.get("DISCORD_TOKEN", "").strip()
    if not token:
        try:
            token = (base_dir / "token.txt").read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            pass
    if not token:
        raise RuntimeError("Configure DISCORD_TOKEN ou un fichier token.txt non vide à côté de sataniawabot.py.")
    client_id = env.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = env.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if bool(client_id) != bool(client_secret):
        raise RuntimeError("SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET doivent être configurés ensemble.")
    return Config(
        token, env.get("DEEPL_API_KEY", "").strip(), client_id, client_secret, base_dir,
        valheim_server_name=env.get("VALHEIM_SERVER_NAME", "Serveur Gangserv3").strip() or "Serveur Gangserv3",
        valheim_screen_name=env.get("VALHEIM_SCREEN_NAME", "Gangserv3").strip() or "Gangserv3",
    )
