from discord.ext import commands


class TranslationCog(commands.Cog):
    def __init__(self, service):
        self.service = service

    async def _translate(self, ctx, message, language):
        if not message.strip():
            await ctx.send(f"❌ Indique un texte à traduire. Tape `>help {ctx.command.name}`.")
            return
        translation = await self.service.translate(message, language)
        result = f"**{ctx.author.display_name}** : {translation}"
        for offset in range(0, len(result), 2000):
            await ctx.send(result[offset:offset + 2000])

    @commands.command()
    async def jp(self, ctx, *, message: str):
        """Traduit le texte en japonais avec DeepL et affiche le nom de son auteur.
        Utilisation : >jp <texte>
        Exemple : >jp Bonjour tout le monde !
        Nécessite une clé API DeepL configurée.
        """
        await self._translate(ctx, message, "JA")

    @commands.command()
    async def ko(self, ctx, *, message: str):
        """Traduit le texte en coréen avec DeepL et affiche le nom de son auteur.
        Utilisation : >ko <texte>
        Exemple : >ko Bonjour tout le monde !
        Nécessite une clé API DeepL configurée.
        """
        await self._translate(ctx, message, "KO")
