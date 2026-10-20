from discord.ext import commands
from discord.utils import escape_markdown


class ValheimCog(commands.Cog):
    def __init__(self, service):
        self.service = service

    async def send_status(self, ctx):
        running = await self.service.is_running()
        state = "🟢 allumé" if running else "🔴 éteint"
        await ctx.send(f"Le serveur Valheim **{self.service.server_name}** est {state}.")

    @commands.group(invoke_without_command=True)
    async def valheim(self, ctx):
        """Indique si le serveur Valheim est allumé ou éteint.
        Utilisation : >valheim, >valheim status ou >valheim player
        Le serveur peut encore être en cours de démarrage lorsqu’il est indiqué allumé.
        """
        if ctx.subcommand_passed is not None:
            await ctx.send("❌ Sous-commande inconnue. Utilise `>valheim status` ou `>valheim player`.")
            return
        await self.send_status(ctx)

    @valheim.command(aliases=["players"])
    async def player(self, ctx):
        """Affiche la dernière mesure des joueurs connectés et les noms disponibles.
        Utilisation : >valheim player (ou >valheim players)
        Les informations sont actualisées environ toutes les dix minutes.
        L’heure affichée est celle du serveur ; les noms peuvent être indisponibles.
        """
        snapshot = await self.service.players()
        message = f"👥 **{snapshot.count} joueur(s)** sur **{escape_markdown(self.service.server_name)}**."
        if snapshot.names:
            message += "\n" + "\n".join(f"• {escape_markdown(name)[:100]}" for name in snapshot.names[:20])
        elif snapshot.count:
            message += "\nLes noms des joueurs ne sont pas disponibles."
        message += f"\nDernière mesure : {snapshot.reported_at} (heure du serveur, actualisation ≈ 10 min)."
        await ctx.send(message)

    @valheim.command()
    async def status(self, ctx):
        """Indique si le serveur Valheim est allumé ou éteint.
        Utilisation : >valheim status
        """
        await self.send_status(ctx)
