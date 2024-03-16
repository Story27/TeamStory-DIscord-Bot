import discord
from discord.ext import commands
import json
import os
import asyncio

class Strikes(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.strikes_db = {}  # Dictionary to store user strikes
        self.banned_words_db = {}  # Dictionary to store banned words for each server
        self.thresholds = {}  # Dictionary to store thresholds for each action
        self.muted_role_name = "Muted"  # Name of the muted role

        # Load strikes database, banned words, and thresholds for each server
        self.load_strikes()
        self.load_banned_words()
        self.load_thresholds()

    # Load Banned Words Database-----------------------------------------------------
    def load_banned_words(self):
        if not os.path.exists('banned_words.json'):
            with open('banned_words.json', 'w') as file:
                json.dump({}, file)
        try:
            with open('banned_words.json', 'r') as file:
                self.banned_words_db = json.load(file)
        except json.JSONDecodeError:
            self.banned_words_db = {}

    # Load Thresholds Database--------------------------------------------------------
    def load_thresholds(self):
        if not os.path.exists('thresholds'):
            os.makedirs('thresholds')

    def load_server_thresholds(self, guild_id):
        file_path = f'thresholds/{guild_id}.json'
        if not os.path.exists(file_path):
            self.thresholds[guild_id] = {'tempmute': {'strikes': 3, 'duration': 1800}, 
                                          'mute': {'strikes': 5, 'duration': 86400}, 
                                          'tempban': {'strikes': 7, 'duration': 604800}, 
                                          'ban': {'strikes': 10}}
            self.save_server_thresholds(guild_id)
        else:
            with open(file_path, 'r') as file:
                self.thresholds[guild_id] = json.load(file)

    def save_server_thresholds(self, guild_id):
        file_path = f'thresholds/{guild_id}.json'
        with open(file_path, 'w') as file:
            json.dump(self.thresholds[guild_id], file, indent=4)

    # Load Strikes Database-----------------------------------------------------------
    def load_strikes(self):
        if not os.path.exists('strikes.json'):
            with open('strikes.json', 'w') as file:
                json.dump({}, file)
        try:
            with open('strikes.json', 'r') as file:
                self.strikes_db = json.load(file)
        except json.JSONDecodeError:
            self.strikes_db = {}

    # Save Strikes to JSON file--------------------------------------------------------
    async def save_strikes(self):
        with open('strikes.json', 'w') as file:
            json.dump(self.strikes_db, file, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return

        # Get the command prefix string by calling the function
        prefix = self.client.command_prefix(self.client, message)
        
        # Check if the message starts with the command prefix
        if message.content.startswith(prefix):
            return

        guild_id = str(message.guild.id)
        author_id = str(message.author.id)

        if guild_id not in self.thresholds:
            self.load_server_thresholds(guild_id)

        if guild_id in self.banned_words_db:
            for word in self.banned_words_db[guild_id]:
                if word.lower() in message.content.lower():
                    await message.delete()
                    embed = discord.Embed(title="Banned Words",
                                        description=f"{message.author.mention}, the word '{word}' is banned in this server.",
                                        color=discord.Color.red())
                    await message.channel.send(embed=embed, delete_after=5)

                    # Update strikes for the user
                    previous_strikes = self.strikes_db.get(author_id, 0)
                    new_strikes = previous_strikes + 1
                    self.strikes_db[author_id] = new_strikes
                    await self.save_strikes()
                    
                    # Send DM with updated strikes count
                    await self.send_strikes_dm(message.author, new_strikes)
                    
                    # Check if any action needs to be taken based on the updated strikes count
                    await self.check_action(message.channel, message.author, new_strikes, guild_id)
                
    async def send_strikes_dm(self, user, strikes_count):
        author_id = str(user.id)
        dm_channel = await user.create_dm()
        embed = discord.Embed(title="Strikes",
                              description=f"You have {strikes_count} strike(s).",
                              color=discord.Color.red())
        try:
            await dm_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # User has disabled DMs or blocked the bot

    @commands.group(name='strikes', invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def strikes(self, ctx):
        embed = discord.Embed(title="Strikes Command",
                              description="Invalid strikes command. Use the following subcommands:",
                              color=discord.Color.red())
        embed.add_field(name="Check Strikes",
                        value="`strikes check <user>`: Check the number of strikes for a user.",
                        inline=False)
        embed.add_field(name="Add Strikes",
                        value="`strikes add <user> <amount>`: Add strikes to a user.",
                        inline=False)
        embed.add_field(name="Remove Strikes",
                        value="`strikes remove <user> <amount>`: Remove strikes from a user.",
                        inline=False)
        await ctx.send(embed=embed)

    @strikes.command(name='check')
    async def check_strikes(self, ctx, user: discord.User):
        user_id = str(user.id)
        if self.strikes_db.get(user_id):
            strikes = self.strikes_db.get(user_id)
        else:
            strikes = 0
        embed = discord.Embed(title="Strikes Command",
                        description=f"{user.mention} has {strikes} strike(s).",
                        color=discord.Color.blue())
        await ctx.send(embed=embed)

    @strikes.command(name='add')
    async def add_strike(self, ctx, user: discord.User, amount: int = 1):
        user_id = str(user.id)

        if self.strikes_db.get(user_id):
            current_strikes = self.strikes_db.get(user_id)
        else:
            current_strikes = 0

        new_strikes = current_strikes + amount

        self.strikes_db[user_id] = new_strikes

        await self.save_strikes()

        embed = discord.Embed(title="Strikes Command",
                            description=f"{amount} strike(s) added to {user.mention}.",
                            color=discord.Color.green())
        await ctx.send(embed=embed)

        # After adding strikes, check if any action needs to be taken
        await self.check_action(ctx, user, new_strikes, str(ctx.guild.id))

    @strikes.command(name='remove')
    async def remove_strike(self, ctx, user: discord.User, amount: int = 1):
        user_id = str(user.id)

        if self.strikes_db.get(user_id) is not None:  # Check if user exists in the database
            current_strikes = self.strikes_db.get(user_id)
        else:
            embed = discord.Embed(title="Strikes Command",
                                description=f"{user.mention} is not in the list.",
                                color=discord.Color.red())
            await ctx.send(embed=embed)
            return  # Exit the function if user is not in the list

        new_strikes = current_strikes - amount
        if new_strikes < 0:
            new_strikes = current_strikes
            embed = discord.Embed(title="Strikes Command",
                                description=f"The number of strikes for {user.mention} cannot go below 0.",
                                color=discord.Color.red())
        else:
            embed = discord.Embed(title="Strikes Command",
                                description=f"{amount} strike(s) removed from {user.mention}.",
                                color=discord.Color.orange())

        self.strikes_db[user_id] = new_strikes
        await self.save_strikes()
        await ctx.send(embed=embed)

        # After removing strikes, check if any action needs to be taken
        await self.check_action(ctx, user, new_strikes, str(ctx.guild.id))

                 
    @strikes.command(name='set')
    @commands.has_permissions(manage_messages=True)
    async def set_threshold(self, ctx, action: str = None, threshold: str = None):
        if action is None or threshold is None:
            embed = discord.Embed(title="Strikes Command",
                                description="Usage: `strikes set_threshold <action> <threshold>`",
                                color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        if action not in self.thresholds[str(ctx.guild.id)]:
            embed = discord.Embed(title="Strikes Command",
                                description="Invalid action. Available actions: tempmute, mute, tempban, ban",
                                color=discord.Color.red())
            await ctx.send(embed=embed)
            return

        self.thresholds[str(ctx.guild.id)][action]['threshold'] = int(threshold)
        self.save_server_thresholds(str(ctx.guild.id))
        embed = discord.Embed(title="Strikes Command",
                            description=f"Threshold for action '{action}' set to '{threshold}'.",
                            color=discord.Color.green())
        await ctx.send(embed=embed)

    async def check_action(self, ctx, user, strikes, guild_id):
        user_id = str(user.id)
        for action, data in self.thresholds[guild_id].items():
            strike_threshold = data['strikes']  # accessing the 'strikes' key instead of 'threshold'
            if isinstance(strike_threshold, int) and strikes == strike_threshold:
                if action == 'tempmute':
                    await self.mute(ctx, user, data['duration'])
                elif action == 'mute':
                    await self.mute(ctx, user, data['duration'])
                elif action == 'tempban':
                    await self.tempban(ctx, user, data['duration'])
                elif action == 'ban':
                    await self.ban(ctx, user)

    async def mute(self, ctx, user, duration):
        muted_role = discord.utils.get(ctx.guild.roles, name=self.muted_role_name)
        if not muted_role:
            muted_role = await ctx.guild.create_role(name=self.muted_role_name)
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)

        await user.add_roles(muted_role)
        embed = discord.Embed(title="Strikes Command",
                            description=f"{user.mention} has been muted for {duration}.",
                            color=discord.Color.orange())
        await ctx.send(embed=embed)

        if duration is not None:
            await asyncio.sleep(duration)
            await user.remove_roles(muted_role)

    async def tempban(self, ctx, user, duration):
        await ctx.guild.ban(user)
        embed = discord.Embed(title="Strikes Command",
                            description=f"{user.mention} has been temporarily banned for {duration}.",
                            color=discord.Color.orange())
        await ctx.send(embed=embed)

        if duration is not None:
            await asyncio.sleep(duration)
            await ctx.guild.unban(user)

    async def ban(self, ctx, user):
        await ctx.guild.ban(user)
        embed = discord.Embed(title="Strikes Command",
                            description=f"{user.mention} has been permanently banned.",
                            color=discord.Color.red())
        await ctx.send(embed=embed)

# Setup function
async def setup(client):
    await client.add_cog(Strikes(client))
