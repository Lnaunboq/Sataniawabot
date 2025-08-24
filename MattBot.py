import os
import random
import requests
import discord
from discord.ext import commands
import spotipy  # type: ignore
from spotipy.oauth2 import SpotifyClientCredentials  # type: ignore
from setproctitle import setproctitle # type: ignore

TOKEN = ""
DEEPL_API_KEY = ""
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
)

PLAYLIST_ID = "37i9dQZF1DXcBWIGoYBM5M"  # par défaut
PLAYLIST_WEEB = "1slD6f3tiZLLCQXivuAotL"
PLAYLIST_SUSSY = "5A7t2KdFJb9oBeGECBf4Xp"
PLAYLIST_ROCK = "4uBqThgovepwPVCkbsO3lS"

PLAYLISTS = {
    "default": PLAYLIST_ID,
    "weeb": PLAYLIST_WEEB,
    "sussy": PLAYLIST_SUSSY,
    "rock": PLAYLIST_ROCK,
}

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=">", intents=intents, help_command=None)
bot.remove_command("help")

setproctitle("SataniawaBot")

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")


# -------------------------------------HELP-------------------------------------


@bot.command()
async def help(ctx, args=None):
    help_embed = discord.Embed(title="Help command")
    command_names_list = [x.name for x in bot.commands]

    # If there are no arguments, just list the commands:
    if not args:
        help_embed.add_field(
            name="List of supported commands:",
            value="\n".join(
                [str(i + 1) + ". " + x.name for i, x in enumerate(bot.commands)]
            ),
            inline=False,
        )
        help_embed.add_field(
            name="Details",
            value="Type `>help <command name>` for more details about each command.",
            inline=False,
        )

    # If the argument is a command, get the help text from that command:
    elif args in command_names_list:
        help_embed.add_field(name=args, value=bot.get_command(args).help)

    # If someone is just trolling:
    else:
        help_embed.add_field(name="Nope.", value="oui oui aller")

    await ctx.send(embed=help_embed)


# -----------------------------TRADUCTIONS-JP--------------------------------------


def translate_text_deepl(text, target_lang):
    url = "https://api-free.deepl.com/v2/translate"
    data = {"auth_key": DEEPL_API_KEY, "text": text, "target_lang": target_lang.upper()}

    try:
        with requests.post(url, data=data, timeout=10) as response:
            print(f"↩️ DeepL status code: {response.status_code}")
            print(f"↩️ DeepL response: {response.text}")

            if response.status_code == 200:
                result = response.json()
                return result["translations"][0]["text"]
            else:
                return f"❌ Erreur DeepL : {response.status_code}"
    except Exception as e:
        print(f"❌ Exception dans translate_text_deepl: {e}")
        return "❌ Erreur réseau ou DeepL."


# Japan
@bot.command()
async def jp(ctx, *, message: str):
    # await ctx.message.delete()
    traduction = translate_text_deepl(message, "JA")
    await ctx.send(f"**{ctx.author.display_name}** : {traduction}")


# Korea
@bot.command()
async def ko(ctx, *, message: str):
    traduction = translate_text_deepl(message, "KO")
    await ctx.send(f"**{ctx.author.display_name}** : {traduction}")


# -------------------------------------SUSHI-------------------------------------


@bot.command()
async def sushi(ctx):
    folder = "images/sushis"
    files = os.listdir(folder)
    if not files:
        return await ctx.send("❌ Aucun sushi trouvé dans le dossier.")
    file = random.choice(files)
    path = os.path.join(folder, file)
    await ctx.send(file=discord.File(path))


# -------------------------------------SPOTIFY-------------------------------------


@bot.command()
async def music(ctx, playlist: str = "default"):
    playlist = playlist.lower()

    # Si l'utilisateur veut la liste
    if playlist == "list":
        playlists_text = "\n".join([f"- **{name}**" for name in PLAYLISTS.keys()])
        return await ctx.send(f"📂 Playlists disponibles :\n{playlists_text}")

    # Vérification que la playlist existe
    if playlist not in PLAYLISTS:
        return await ctx.send(
            f"❌ Playlist inconnue : {playlist}. Tape `>music list` pour voir les playlists dispo."
        )

    # Récupération des titres
    results = sp.playlist_items(PLAYLISTS[playlist], additional_types=["track"])
    tracks = results["items"]

    if not tracks:
        return await ctx.send("❌ Aucun titre trouvé dans cette playlist.")

    track = random.choice(tracks)["track"]
    track_name = track["name"]
    artists = ", ".join([artist["name"] for artist in track["artists"]])
    track_url = track["external_urls"]["spotify"]

    await ctx.send(f"🎵 **{track_name}** par {artists}\n{track_url}")


# -------------------------------------ANIME-------------------------------------


@bot.command()
async def anime(ctx):
    await ctx.send(f"anime")


# -------------------------------------DONNEAVIS-------------------------------------


# def get_random_avis():
#     try:
#         with open("avis.json", "r", encoding="utf-8") as file:
#             data = json.load(file)
#             phrases = data.get("phrases", [])
#             if phrases:
#                 return random.choice(phrases)
#             else:
#                 return "!donneavis sur le fait que le fichier soit vide, y'a pas d'avis à donner."
#     except Exception as e:
#         print(f"Erreur lors de la lecture d'avis.json : {e}")
#         return "erreur lors de la lecture des avis."

# @bot.command()
# async def avis(ctx):
#     phrase = get_random_avis()
#     await ctx.send(f"!donneavis sur {phrase}")

# ------------------------------------GESTION-SERVEURS-------------------------------------

# class LeaveGuildView(View):
#     def __init__(self, bot, guilds):
#         super().__init__(timeout=60)
#         self.bot = bot
#         self.guild_map = {f"{g.name} (ID: {g.id})": g for g in guilds}

#         options = [
#             discord.SelectOption(
#                 label=g.name, description=f"ID: {g.id}", value=str(g.id)
#             )
#             for g in guilds
#         ]

#         self.select = Select(
#             placeholder="Choisis un serveur à quitter", options=options
#         )
#         self.select.callback = self.select_callback
#         self.add_item(self.select)

#         self.quit_button = Button(
#             label="Quitter le serveur sélectionné", style=discord.ButtonStyle.danger
#         )
#         self.quit_button.callback = self.leave_callback
#         self.quit_button.disabled = True
#         self.add_item(self.quit_button)

#         self.selected_guild_id = None

#     async def select_callback(self, interaction: discord.Interaction):
#         self.selected_guild_id = int(self.select.values[0])
#         self.quit_button.disabled = False
#         await interaction.response.edit_message(
#             content=f"✅ Serveur sélectionné : `{self.selected_guild_id}`", view=self
#         )

#     async def leave_callback(self, interaction: discord.Interaction):
#         guild = self.bot.get_guild(self.selected_guild_id)
#         if guild:
#             await guild.leave()
#             await interaction.response.edit_message(
#                 content=f"🚪 Le bot a quitté **{guild.name}**", view=None
#             )
#         else:
#             await interaction.response.send_message(
#                 "❌ Le bot n'est plus dans ce serveur.", ephemeral=True
#             )

# @bot.command()
# @commands.is_owner()
# async def serveurs(ctx):
#     guilds = bot.guilds
#     if not guilds:
#         await ctx.send("Le bot n'est dans aucun serveur.")
#         return

#     view = LeaveGuildView(bot, guilds)
#     await ctx.send("🔽 Sélectionne un serveur à quitter :", view=view)

# -------------------------------------------------------------------------------

bot.run(TOKEN)
