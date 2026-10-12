"""État du processus SteamCMD local, y compris lorsqu’il tourne dans screen."""
import asyncio
from pathlib import Path

from .errors import ServiceError


class ValheimService:
    def __init__(self, server_name, proc_dir=Path("/proc")):
        self.server_name = server_name
        self.proc_dir = Path(proc_dir)

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
