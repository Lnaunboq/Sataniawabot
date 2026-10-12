from discord.ext import commands


class MusicCog(commands.Cog):
    def __init__(self, service, playlists):
        self.service = service
        self.playlists = playlists

    @commands.command()
    async def music(self, ctx, playlist: str = "default"):
        """Partage un titre choisi au hasard dans toute une playlist Spotify.
        Utilisation : >music [playlist]
        Playlists : default (par défaut), weeb, sussy, rock.
        >music list affiche les playlists disponibles.
        Exemple : >music rock
        Nécessite Spotify configuré pour choisir un titre.
        """
        playlist = playlist.lower()
        if playlist == "list":
            await ctx.send("📂 Playlists disponibles :\n" + "\n".join(f"- **{name}**" for name in self.playlists))
            return
        if playlist not in self.playlists:
            await ctx.send(f"❌ Playlist inconnue : {playlist}. Tape `>music list` pour voir les playlists disponibles.")
            return
        track = await self.service.random_track(self.playlists[playlist])
        await ctx.send(f"🎵 **{track.name}** par {track.artists}\n{track.url}")
