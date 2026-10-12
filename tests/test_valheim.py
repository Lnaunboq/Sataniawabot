from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sataniawabot.config import load_config
from sataniawabot.services.errors import ServiceError
from sataniawabot.services.valheim import ValheimService


class ValheimTests(unittest.TestCase):
    def test_configuration(self):
        self.assertEqual(load_config({"DISCORD_TOKEN": "test"}).valheim_server_name, "Serveur Gangserv3")
        self.assertEqual(load_config({"DISCORD_TOKEN": "test", "VALHEIM_SERVER_NAME": "Autre"}).valheim_server_name, "Autre")

    def test_actual_server_name_and_other_running_server(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            service = ValheimService(load_config({"DISCORD_TOKEN": "test"}).valheim_server_name, root)
            other = root / "229394"
            other.mkdir()
            (other / "cmdline").write_bytes(b"./valheim_server.x86_64\0-name\0Serveur Gangserv2\0")
            self.assertFalse(service._is_running())
            target = root / "229926"
            target.mkdir()
            (target / "cmdline").write_bytes(b"./valheim_server.x86_64\0-name\0Serveur Gangserv3\0")
            self.assertTrue(service._is_running())
            (target / "cmdline").unlink()
            self.assertFalse(service._is_running())

    def test_process_matching(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            process = root / "123"
            process.mkdir()
            service = ValheimService("Gangserv3", root)
            self.assertFalse(service._is_running())
            for command, expected in [
                (b"/srv/valheim_server.x86_64\0-name\0Gangserv3\0-password\0secret\0", True),
                (b"valheim_server.x86_64\0-name\0Autre\0", False),
                (b"screen\0-name\0Gangserv3\0", False),
                (b"valheim_server.x86_64\0-name\0", False),
                (b"", False),
            ]:
                (process / "cmdline").write_bytes(command)
                self.assertEqual(service._is_running(), expected)

    def test_unreadable_process_is_not_reported_as_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "123").mkdir()
            with patch.object(Path, "read_bytes", side_effect=PermissionError):
                with self.assertRaises(ServiceError):
                    ValheimService("Gangserv3", folder)._is_running()
        with self.assertRaises(ServiceError):
            ValheimService("Gangserv3", Path(folder))._is_running()
