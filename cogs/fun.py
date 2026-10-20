import discord
from discord.ext import commands


class FunCog(commands.Cog):
    def __init__(self, service):
        self.service = service

    @commands.command()
    async def sushi(self, ctx):
        """Recherche une image de sushi sur Internet et l’affiche sans l’enregistrer.
        Utilisation : >sushi
        Source : TheMealDB ; aucun compte ni clé personnelle nécessaire.
        """
        image = await self.service.random_image()
        embed = discord.Embed(
            title="🍣 Sushi", url=image.source,
            description=f"[Source : TheMealDB]({image.source})",
        )
        embed.set_image(url=image.url)
        await ctx.send(embed=embed)
