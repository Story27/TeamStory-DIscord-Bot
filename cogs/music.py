import discord
from discord.ext import commands
import wavelink
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from discord import FFmpegPCMAudio

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET"
        ))
        self.music_queue = []

    @commands.Cog.listener()
    async def on_ready(self):
        await self.client.wavelink.initiate_node(host='localhost', port=2333, rest_uri='http://localhost:2333', password='youshallnotpass')

    @commands.command(name="join", help="Joins the voice channel the user is in")
    async def join(self, ctx):
        voice_channel = ctx.author.voice.channel
        if voice_channel:
            await voice_channel.connect()
            await ctx.send(f"Connected to {voice_channel}")
        else:
            await ctx.send(f"You are not in any Voice Channels.")

    @commands.command(name="play", help="Plays a selected song from Spotify")
    async def play(self, ctx, *args):
        query = " ".join(args)
        
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.send("Connect to a voice channel!")
            return

        tracks = self.spotify.search(query, limit=1, type='track')['tracks']['items']

        if not tracks:
            await ctx.send("No tracks found with the given query.")
            return

        track = tracks[0]
        self.music_queue.append(track)

        if not self.client.wavelink.nodes:
            await ctx.send("Bot is not connected to any voice nodes.")
            return

        if not ctx.voice_client:
            vc = await voice_channel.connect()
        else:
            vc = ctx.voice_client

        if not vc.is_playing():
            await self.play_track(vc)

    async def play_track(self, vc):
        if not self.music_queue:
            return

        track = self.music_queue.pop(0)
        track_url = track['external_urls']['spotify']
        source = await self.client.wavelink.get_tracks(f'ytsearch:{track_url}')

        vc.play(source[0], after=lambda e: self.play_track(vc))

    @commands.command(name="pause", help="Pauses the currently playing song")
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await ctx.send("Song paused")

    @commands.command(name="skip", help="Skips the currently playing song")
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc and vc.is_playing():
            vc.stop()
            await ctx.send("Song skipped")

    @commands.command(name="queue", help="Displays the current songs in queue")
    async def queue(self, ctx):
        if self.music_queue:
            queue_list = "\n".join([track['name'] for track in self.music_queue])
            await ctx.send(f"Queue:\n{queue_list}")
        else:
            await ctx.send("Queue is empty")

    @commands.command(name="qclear", help="Clears the music queue")
    async def clear(self, ctx):
        self.music_queue.clear()
        await ctx.send("Queue cleared")

    @commands.command(name="leave", help="Leaves the voice channel")
    async def leave(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.disconnect()
            await ctx.send("Left the voice channel")
        else:
            await ctx.send("I'm not in a voice channel.")

async def setup(client):
    await client.add_cog(Music(client))
