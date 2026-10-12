"""Configuration chargée explicitement au démarrage."""
import os
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
    valheim_server_name: str = "Gangserv3"

    @property
    def sushi_dir(self):
        return self.base_dir / "images" / "sushis"

    @property
    def data_dir(self):
        return self.base_dir / "data"


def load_config(environ=None, base_dir=BASE_DIR):
    env = os.environ if environ is None else environ
    base_dir = Path(base_dir).resolve()
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
        valheim_server_name=env.get("VALHEIM_SERVER_NAME", "Gangserv3").strip() or "Gangserv3",
    )
