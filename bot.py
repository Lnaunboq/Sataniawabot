"""Composition du bot, cycle de vie HTTP et gestion commune des erreurs."""
import logging
import aiohttp
import discord
from discord.ext import commands

if __package__:
    from .cogs.fun import FunCog
    from .cogs.help import HelpCog
    from .cogs.music import MusicCog
    from .cogs.translation import TranslationCog
    from .services.deepl import DeepLService
    from .services.errors import ServiceError
    from .services.spotify import SpotifyService
else:
    from cogs.fun import FunCog
    from cogs.help import HelpCog
    from cogs.music import MusicCog
    from cogs.translation import TranslationCog
    from services.deepl import DeepLService
    from services.errors import ServiceError
    from services.spotify import SpotifyService

logger = logging.getLogger(__name__)


class SataniawaBot(commands.Bot):
    def __init__(self, config):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(
            command_prefix=">", intents=intents, help_command=None,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        self.config = config
        self.api_session = None

    async def setup_hook(self):
        self.api_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        await self.add_cog(HelpCog(self))
        await self.add_cog(TranslationCog(
            DeepLService(self.config.deepl_api_key, self.api_session),
        ))
        await self.add_cog(MusicCog(
            SpotifyService.from_config(self.config), self.config.playlists,
        ))
        await self.add_cog(FunCog(self.config.sushi_dir))

    async def close(self):
        try:
            if self.api_session is not None:
                await self.api_session.close()
        finally:
            await super().close()

    async def on_ready(self):
        logger.info("Connecté en tant que %s", self.user)

    async def on_command_error(self, ctx, error):
        if ctx.command and ctx.command.has_error_handler():
            return
        if ctx.cog and ctx.cog.has_error_handler():
            return
        cause = getattr(error, "original", error)
        if isinstance(cause, ServiceError):
            message = f"❌ {cause}"
        elif isinstance(error, commands.CommandNotFound):
            message = "❌ Commande inconnue. Tape `>help` pour voir les commandes disponibles."
        elif isinstance(error, commands.UserInputError):
            message = f"❌ Arguments manquants ou invalides. Tape `>help {ctx.command.name}` pour voir la syntaxe."
        elif isinstance(error, commands.CheckFailure):
            message = "❌ Tu ne peux pas utiliser cette commande ici."
        else:
            logger.error(
                "Échec de la commande %s (%s)",
                getattr(ctx.command, "name", "inconnue"), type(cause).__name__,
            )
            message = "❌ Une erreur est survenue pendant la commande."
        await ctx.send(message)
