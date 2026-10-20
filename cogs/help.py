import discord
from discord.ext import commands


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *, command_name=None):
        """Affiche les commandes disponibles ou l’aide détaillée d’une commande.
        Utilisation : >help [commande]
        Exemples : >help music, >help valheim player
        """
        embed = discord.Embed(title="Aide des commandes")
        if command_name is None:
            for command in sorted(self.bot.commands, key=lambda command: command.name):
                if not command.hidden:
                    embed.add_field(name=f">{command.name}", value=command.short_doc or "Aucune description disponible.", inline=False)
            embed.set_footer(text="Tape >help <commande> pour consulter son utilisation et ses détails.")
        else:
            command = self.bot.get_command(command_name)
            if command is None or command.hidden:
                embed.add_field(name="Commande inconnue", value="Tape `>help` pour voir les commandes disponibles.")
            else:
                embed.add_field(name=command.name, value=command.help or "Aucune description disponible.", inline=False)
        await ctx.send(embed=embed)
