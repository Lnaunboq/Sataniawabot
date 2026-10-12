from discord.ext import commands


class ValheimCog(commands.Cog):
    def __init__(self, service):
        self.service = service

    async def send_status(self, ctx):
        running = await self.service.is_running()
        state = "🟢 allumé" if running else "🔴 éteint"
        await ctx.send(f"Le serveur Valheim **{self.service.server_name}** est {state}.")

    @commands.group(invoke_without_command=True)
    async def valheim(self, ctx):
        """Affiche si le processus du serveur Valheim local est lancé.
        Utilisation : >valheim ou >valheim status
        Le statut indique le processus lancé, pas la disponibilité du monde en jeu.
        """
        if ctx.subcommand_passed is not None:
            await ctx.send("❌ Sous-commande inconnue. Utilise `>valheim status`.")
            return
        await self.send_status(ctx)

    @valheim.command()
    async def status(self, ctx):
        """Affiche si le processus du serveur Valheim local est lancé.
        Utilisation : >valheim status
        """
        await self.send_status(ctx)
