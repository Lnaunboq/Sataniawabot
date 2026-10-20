import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

from discord.ext import commands

from sataniawabot.bot import SataniawaBot
from sataniawabot.config import BASE_DIR, Config, load_config
from sataniawabot.cogs.fun import FunCog
from sataniawabot.services.deepl import DeepLService
from sataniawabot.services.errors import EmptyPlaylist, NotConfigured, ServiceError
from sataniawabot.services.spotify import SpotifyService


class ConfigTests(unittest.TestCase):
    def test_token_sources_and_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(RuntimeError):
                load_config({}, folder)
            path = Path(folder) / "token.txt"
            path.write_text(" \n")
            with self.assertRaises(RuntimeError):
                load_config({}, folder)
            path.write_text("file-token\n")
            self.assertEqual(load_config({}, folder).token, "file-token")
            config = load_config({"DISCORD_TOKEN": "env-token"}, folder)
            self.assertEqual(config.token, "env-token")
            self.assertNotIn("env-token", repr(config))
            with self.assertRaises(RuntimeError):
                load_config({"DISCORD_TOKEN": "token", "SPOTIFY_CLIENT_ID": "id"}, folder)

    def test_import_from_other_directory_without_token_or_connection(self):
        script = """
import runpy
from unittest.mock import patch
with patch('pathlib.Path.read_text', side_effect=AssertionError('secret read')), patch('discord.ext.commands.Bot.run', side_effect=AssertionError('connection')):
    runpy.run_path(SCRIPT, run_name='import_check')
from config import Config, BASE_DIR
assert Config('test').sushi_dir == BASE_DIR / 'images' / 'sushis'
assert list(Config('test').sushi_dir.glob('*.webp'))
""".replace("SCRIPT", repr(str(BASE_DIR / "sataniawabot.py")))
        env = dict(os.environ, PYTHONPATH=str(BASE_DIR), PYTHONDONTWRITEBYTECODE="1")
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run([sys.executable, "-c", script], cwd=folder, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_deepl_missing_key_and_success(self):
        session = Mock()
        with self.assertRaises(NotConfigured):
            await DeepLService("", session).translate("bonjour", "JA")
        session.post.assert_not_called()
        response = SimpleNamespace(status=200, json=AsyncMock(return_value={"translations": [{"text": "こんにちは"}]}))
        manager = Mock(__aenter__=AsyncMock(return_value=response), __aexit__=AsyncMock(return_value=False))
        session.post.return_value = manager
        service = DeepLService("test:fx", session)
        self.assertEqual(await service.translate("bonjour", "ja"), "こんにちは")
        self.assertIn("api-free.deepl.com", session.post.call_args.args[0])
        self.assertEqual(session.post.call_args.kwargs["data"]["target_lang"], "JA")
        self.assertEqual(session.post.call_args.kwargs["timeout"].total, 10)

    async def test_deepl_api_invalid_payload_and_timeout(self):
        response = SimpleNamespace(status=403, json=AsyncMock())
        session = Mock()
        session.post.return_value = Mock(__aenter__=AsyncMock(return_value=response), __aexit__=AsyncMock(return_value=False))
        service = DeepLService("key", session)
        with self.assertRaisesRegex(ServiceError, "403"):
            await service.translate("texte", "KO")
        response.status = 200
        response.json.return_value = {"translations": []}
        with self.assertRaisesRegex(ServiceError, "invalide"):
            await service.translate("texte", "KO")
        session.post.side_effect = asyncio.TimeoutError
        with self.assertRaisesRegex(ServiceError, "délai"):
            await service.translate("texte", "KO")

    async def test_spotify_all_pages_and_invalid_tracks(self):
        valid = {"name": "Titre", "artists": [{"name": "Artiste"}], "external_urls": {"spotify": "https://example.test/track"}}
        client = Mock()
        client.playlist_items.return_value = {"items": [{"track": None}, {"track": {"name": "incomplet"}}], "next": "page2"}
        client.next.return_value = {"items": [{"track": valid}, {"track": dict(valid, is_local=True)}], "next": None}
        service = SpotifyService(client)
        with patch("sataniawabot.services.spotify.random.choice", side_effect=lambda tracks: tracks[0]) as choose:
            track = await service.random_track("playlist")
            self.assertEqual(len(choose.call_args.args[0]), 1)
        self.assertEqual((track.name, track.artists), ("Titre", "Artiste"))
        client.next.assert_called_once()

    async def test_spotify_missing_empty_and_network_error(self):
        with self.assertRaises(NotConfigured):
            await SpotifyService().random_track("playlist")
        client = Mock()
        client.playlist_items.return_value = {"items": [], "next": None}
        with self.assertRaises(EmptyPlaylist):
            await SpotifyService(client).random_track("playlist")
        import requests
        client.playlist_items.side_effect = requests.Timeout
        with self.assertRaises(ServiceError):
            await SpotifyService(client).random_track("playlist")

    async def test_spotify_does_not_block_event_loop(self):
        import threading
        started, release = threading.Event(), threading.Event()
        def blocking_call(*args, **kwargs):
            started.set()
            release.wait(2)
            return {"items": [], "next": None}
        client = Mock()
        client.playlist_items.side_effect = blocking_call
        task = asyncio.create_task(SpotifyService(client).random_track("playlist"))
        try:
            await asyncio.wait_for(asyncio.to_thread(started.wait, 1), 1.5)
            self.assertTrue(started.is_set())
            self.assertFalse(task.done())
        finally:
            release.set()
            with self.assertRaises(EmptyPlaylist):
                await task


class CommandTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = SataniawaBot(Config("test"))
        await self.bot.setup_hook()
        self.ctx = SimpleNamespace(send=AsyncMock(), author=SimpleNamespace(display_name="Auteur"), command=None, cog=None)

    async def asyncTearDown(self):
        session = self.bot.api_session
        await self.bot.close()
        self.assertTrue(session.closed)

    async def invoke(self, name, *args, **kwargs):
        command = self.bot.get_command(name)
        self.ctx.command, self.ctx.cog = command, command.cog
        return await command.callback(command.cog, self.ctx, *args, **kwargs)

    async def test_commands_and_help(self):
        self.assertEqual({c.name for c in self.bot.commands}, {"help", "jp", "ko", "sushi", "music", "valheim"})
        await self.invoke("help")
        self.assertEqual(len(self.ctx.send.call_args.kwargs["embed"].fields), 6)
        for command in self.bot.commands:
            self.assertTrue(command.help)
            await self.invoke("help", command.name)
            field = self.ctx.send.call_args.kwargs["embed"].fields[0]
            self.assertTrue(field.value)
            self.assertLessEqual(len(field.value), 1024)
        await self.invoke("help", "inconnue")
        self.assertEqual(self.ctx.send.call_args.kwargs["embed"].fields[0].name, "Commande inconnue")

    async def test_music_list_unknown_and_unconfigured(self):
        await self.invoke("music", "list")
        self.assertIn("rock", self.ctx.send.call_args.args[0])
        await self.invoke("music", "inconnue")
        self.assertIn("Playlist inconnue", self.ctx.send.call_args.args[0])
        with self.assertRaises(NotConfigured) as error:
            await self.invoke("music")
        await self.bot.on_command_error(self.ctx, commands.CommandInvokeError(error.exception))
        self.assertIn("Spotify n’est pas configuré", self.ctx.send.call_args.args[0])

    async def test_valheim_status_and_unknown_subcommand(self):
        cog = self.bot.get_cog("ValheimCog")
        cog.service = SimpleNamespace(server_name="Gangserv3", is_running=AsyncMock(return_value=True))
        self.ctx.subcommand_passed = None
        await self.invoke("valheim")
        self.assertIn("Gangserv3** est 🟢 allumé", self.ctx.send.call_args.args[0])
        cog.service.is_running.return_value = False
        await self.invoke("valheim status")
        self.assertIn("🔴 éteint", self.ctx.send.call_args.args[0])
        cog.service.is_running.reset_mock()
        self.ctx.subcommand_passed = "inconnue"
        await self.invoke("valheim")
        cog.service.is_running.assert_not_awaited()
        self.assertIn("Sous-commande inconnue", self.ctx.send.call_args.args[0])

    async def test_valheim_player(self):
        from sataniawabot.services.valheim import PlayerSnapshot
        cog = self.bot.get_cog("ValheimCog")
        cog.service = SimpleNamespace(
            server_name="Serveur Gangserv3",
            players=AsyncMock(return_value=PlayerSnapshot(1, ("Viking",), "10/12/2026 21:35:50")),
        )
        await self.invoke("valheim player")
        self.assertIn("1 joueur(s)", self.ctx.send.call_args.args[0])
        self.assertIn("Viking", self.ctx.send.call_args.args[0])
        self.assertIn("10/12/2026 21:35:50", self.ctx.send.call_args.args[0])
        self.assertIs(self.bot.get_command("valheim players"), self.bot.get_command("valheim player"))
        cog.service.players.return_value = PlayerSnapshot(0, (), "10/12/2026 21:45:50")
        await self.invoke("valheim players")
        self.assertIn("0 joueur(s)", self.ctx.send.call_args.args[0])
        cog.service.players.side_effect = ServiceError("Console indisponible")
        with self.assertRaises(ServiceError) as error:
            await self.invoke("valheim player")
        await self.bot.on_command_error(self.ctx, commands.CommandInvokeError(error.exception))
        self.assertIn("Console indisponible", self.ctx.send.call_args.args[0])

    async def test_translation_and_long_result(self):
        cog = self.bot.get_cog("TranslationCog")
        cog.service = SimpleNamespace(translate=AsyncMock(return_value="あ" * 2100))
        await self.invoke("jp", message="bonjour")
        cog.service.translate.assert_awaited_once_with("bonjour", "JA")
        self.assertEqual(self.ctx.send.await_count, 2)
        self.assertTrue(all(len(call.args[0]) <= 2000 for call in self.ctx.send.call_args_list))
        cog.service.translate.reset_mock()
        await self.invoke("ko", message=" ")
        cog.service.translate.assert_not_awaited()

    async def test_missing_argument_and_unknown_command(self):
        self.ctx.command = self.bot.get_command("jp")
        parameter = self.ctx.command.clean_params["message"]
        await self.bot.on_command_error(self.ctx, commands.MissingRequiredArgument(parameter))
        self.assertIn(">help jp", self.ctx.send.call_args.args[0])
        self.ctx.command = None
        await self.bot.on_command_error(self.ctx, commands.CommandNotFound())
        self.assertIn("Commande inconnue", self.ctx.send.call_args.args[0])

    async def test_sushi_missing_empty_and_valid_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            cog = FunCog(Path(folder) / "absent")
            await cog.sushi.callback(cog, self.ctx)
            self.assertIn("Aucun sushi", self.ctx.send.call_args.args[0])
            cog.sushi_dir = Path(folder)
            (Path(folder) / "notes.txt").write_text("pas une image")
            await cog.sushi.callback(cog, self.ctx)
            self.assertIn("Aucun sushi", self.ctx.send.call_args.args[0])
            (Path(folder) / "image.png").write_bytes(b"fake image")
            await cog.sushi.callback(cog, self.ctx)
            self.assertEqual(self.ctx.send.call_args.kwargs["file"].filename, "image.png")
