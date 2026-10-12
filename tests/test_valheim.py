from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
from types import SimpleNamespace

from sataniawabot.config import load_config
from sataniawabot.services.errors import ServiceError
from sataniawabot.services.valheim import ValheimService, parse_players


class ValheimTests(unittest.TestCase):
    def test_configuration(self):
        self.assertEqual(load_config({"DISCORD_TOKEN": "test"}).valheim_server_name, "Serveur Gangserv3")
        self.assertEqual(load_config({"DISCORD_TOKEN": "test", "VALHEIM_SERVER_NAME": "Autre"}).valheim_server_name, "Autre")
        self.assertEqual(load_config({"DISCORD_TOKEN": "test", "VALHEIM_SCREEN_NAME": "custom"}).valheim_screen_name, "custom")

    def test_player_reports_and_departures(self):
        report = "10/12/2026 21:35:50: Connections {} ZDOS:123 sent:0 recv:0\n"
        text = "Got character ZDOID from Viking : 123:1\n" + report.format(1)
        snapshot = parse_players(text)
        self.assertEqual((snapshot.count, snapshot.names), (1, ("Viking",)))
        # Les événements suivant une mesure ne doivent pas changer ses noms.
        self.assertEqual(parse_players(text + "Got character ZDOID from Autre : 456:1\n"), snapshot)
        text += "Destroying abandoned non persistent zdo 123:1 owner 123\n" + report.format(0)
        self.assertEqual(parse_players(text).count, 0)
        self.assertEqual(parse_players(text).names, ())
        self.assertEqual(parse_players(report.format(2)).names, ())
        with self.assertRaises(ServiceError):
            parse_players(text + "Game server connected\n")
        with self.assertRaises(ServiceError):
            parse_players("console sans compteur")

    def test_screen_snapshot_and_failures(self):
        service = ValheimService("Serveur Gangserv3")
        output = None
        def hardcopy(args, **kwargs):
            nonlocal output
            if args[3:] == ["-Q", "windows"]:
                # screen termine la copie après le retour de -X.
                output.write_text("10/12/2026 21:35:50: Connections 0 ZDOS:123\n")
                return SimpleNamespace(returncode=0)
            self.assertEqual(args[:4], ["screen", "-S", "Gangserv3", "-p"])
            self.assertEqual(kwargs["timeout"], 5)
            output = Path(args[-1])
            return SimpleNamespace(returncode=0)
        with patch("sataniawabot.services.valheim.subprocess.run", side_effect=hardcopy):
            self.assertEqual(service._players().count, 0)
        for failure in (FileNotFoundError(), subprocess.TimeoutExpired("screen", 5)):
            with patch("sataniawabot.services.valheim.subprocess.run", side_effect=failure):
                with self.assertRaises(ServiceError):
                    service._players()
        with patch("sataniawabot.services.valheim.subprocess.run", return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(ServiceError):
                service._players()

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
