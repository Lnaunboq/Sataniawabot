"""État du processus SteamCMD local, y compris lorsqu’il tourne dans screen."""
import asyncio
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import tempfile

from .errors import ServiceError


@dataclass(frozen=True)
class PlayerSnapshot:
    count: int
    names: tuple[str, ...]
    reported_at: str


def parse_players(text):
    """Dernier compteur publié, avec les noms connus à cet instant uniquement."""
    players = {}
    snapshot = None
    for line in text.splitlines():
        if "Game server connected" in line:
            players.clear()
            snapshot = None
        joined = re.search(r"Got character ZDOID from (.+?)\s*:\s*(-?\d+:\d+)", line)
        if joined and joined[2] != "0:0":
            players[joined[2]] = joined[1].strip()
        departed = re.search(r"Destroying abandoned non persistent zdo\s+(-?\d+:\d+)", line)
        if departed:
            players.pop(departed[1], None)
        report = re.search(r"(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}):\s+Connections\s+(\d+)\b", line)
        if report:
            count = int(report[2])
            if count == 0:
                players.clear()
            names = tuple(sorted(players.values())) if len(players) == count else ()
            snapshot = PlayerSnapshot(count, names, report[1])
    if snapshot is None:
        raise ServiceError("Aucune mesure des joueurs disponible dans la console de Gangserv3 pour le moment.")
    return snapshot


class ValheimService:
    def __init__(self, server_name, proc_dir=Path("/proc"), screen_name="Gangserv3"):
        self.server_name = server_name
        self.proc_dir = Path(proc_dir)
        self.screen_name = screen_name
        self._screen_lock = asyncio.Lock()

    async def players(self):
        if not await self.is_running():
            raise ServiceError(f"Le serveur Valheim {self.server_name} est éteint.")
        async with self._screen_lock:
            return await asyncio.to_thread(self._players)

    def _players(self):
        try:
            with tempfile.TemporaryDirectory(prefix="valheim-players-") as folder:
                output = Path(folder) / "console.txt"
                result = subprocess.run(
                    ["screen", "-S", self.screen_name, "-p", "0", "-X", "hardcopy", "-h", str(output)],
                    capture_output=True, timeout=5, check=False,
                )
                if result.returncode != 0:
                    raise ServiceError("Console Valheim inaccessible. Vérifie VALHEIM_SCREEN_NAME et l’utilisateur du bot.")
                # -X revient avant que screen ait fini d’écrire. La requête
                # synchrone suivante attend le traitement de la copie précédente.
                barrier = subprocess.run(
                    ["screen", "-S", self.screen_name, "-Q", "windows"],
                    capture_output=True, timeout=5, check=False,
                )
                if barrier.returncode != 0 or not output.is_file():
                    raise ServiceError("Console Valheim inaccessible. Vérifie VALHEIM_SCREEN_NAME et l’utilisateur du bot.")
                return parse_players(output.read_text(encoding="utf-8", errors="replace"))
        except subprocess.TimeoutExpired:
            raise ServiceError("La lecture de la console Valheim a dépassé le délai autorisé.") from None
        except OSError:
            raise ServiceError("Impossible de lire la console Valheim. Vérifie que screen est installé et accessible.") from None

    async def is_running(self):
        return await asyncio.to_thread(self._is_running)

    def _is_running(self):
        try:
            processes = list(self.proc_dir.iterdir())
        except OSError:
            raise ServiceError("Impossible de consulter les processus du serveur Valheim.") from None
        unreadable = False
        for process in processes:
            if not process.name.isdecimal():
                continue
            try:
                args = (process / "cmdline").read_bytes().split(b"\0")
            except (FileNotFoundError, ProcessLookupError):
                continue  # Le processus peut se terminer pendant la lecture.
            except OSError:
                unreadable = True
                continue
            if not args or args[0].rsplit(b"/", 1)[-1] != b"valheim_server.x86_64":
                continue
            try:
                name = args[args.index(b"-name") + 1]
            except (ValueError, IndexError):
                continue
            if name == self.server_name.encode("utf-8"):
                return True
        if unreadable:
            raise ServiceError("État Valheim indéterminé : certains processus sont inaccessibles.")
        return False
