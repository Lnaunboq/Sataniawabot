import random
import discord
from discord.ext import commands


class FunCog(commands.Cog):
    def __init__(self, sushi_dir):
        self.sushi_dir = sushi_dir

    @commands.command()
    async def sushi(self, ctx):
        """Envoie une image de sushi choisie au hasard dans le dossier images/sushis.
        Utilisation : >sushi
        """
        try:
            image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            files = [
                path for path in self.sushi_dir.iterdir()
                if path.is_file() and path.suffix.lower() in image_extensions
            ]
        except FileNotFoundError:
            files = []
        if not files:
            await ctx.send("❌ Aucun sushi trouvé dans le dossier.")
            return
        image = discord.File(random.choice(files))
        try:
            await ctx.send(file=image)
        finally:
            image.close()
