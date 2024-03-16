import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime, timedelta

class Strikes(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.strikes_db = {}  # Dictionary to store user strikes
        self.banned_words_db = {}  # Dictionary to store banned words for each server
        self.thresholds = {}  # Dictionary to store thresholds for each action
        self.muted_role_name = "Muted"  # Name of the muted role
        self.spam_messages = {}  # Dictionary to store spam messages data

        # Load strikes database, banned words, and thresholds for each server
        self.load_strikes()
        self.load_banned_words()
        self.load_spam_messages()

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
    def load_thresholds(self, guild_id):
        if guild_id not in self.thresholds:
            file_path = f'thresholds/{guild_id}.json'
            if not os.path.exists(file_path):
                self.thresholds[guild_id] = {'tempmute': {'strikes': 3, 'duration': 1800}, 
                                            'mute': {'strikes': 5, 'duration': 86400}, 
                                            'tempban': {'strikes': 7, 'duration': 604800}, 
                                            'ban': {'strikes': 10},
                                            'spam': {'messages': 5, 'duration': 10}}  # Add spam detection threshold
                self.save_server_thresholds(guild_id)
            else:
                with open(file_path, 'r') as file:
                    self.thresholds[guild_id] = json.load(file)

    def save_server_thresholds(self, guild_id):
        file_path = f'thresholds/{guild_id}.json'
        with open(file_path, 'w') as file:
            json.dump(self.thresholds[guild_id], file, indent=4)

    # Load Spam Messages Database-----------------------------------------------------
    def load_spam_messages(self):
        if not os.path.exists('spam_messages.json'):
            with open('spam_messages.json', 'w') as file:
                json.dump({}, file)
        try:
            with open('spam_messages.json', 'r') as file:
                self.spam_messages = json.load(file)
        except json.JSONDecodeError:
            self.spam_messages = {}

    def save_spam_messages(self):
        current_time = datetime.now()
        # Filter out spam messages older than 2 minutes
        filtered_spam_messages = {
            author_id: [str(time) for time in message_times if current_time - datetime.fromisoformat(time) <= timedelta(minutes=2)]
            for author_id, message_times in self.spam_messages.items()
        }

        with open('spam_messages.json', 'w') as file:
            json.dump(filtered_spam_messages, file, indent=4)

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

    async def add_spam_strike(self, user):
        user_id = str(user.id)
        # Update strikes for the user
        previous_strikes = self.strikes_db.get(user_id, 0)
        new_strikes = previous_strikes + 1
        self.strikes_db[user_id] = new_strikes
        await self.save_strikes()
    
        # Send DM with updated strikes count
        await self.send_strikes_dm(user, new_strikes)
    
        # Check if any action needs to be taken based on the updated strikes count
        guild_id = str(user.guild.id)
        await self.check_action(user.guild.system_channel, user, new_strikes, guild_id)

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
            self.load_thresholds(guild_id)
            
        # Get the author ID
        author_id = str(message.author.id)

        # Ensure author_id is present in self.spam_messages
        if author_id not in self.spam_messages:
            self.spam_messages[author_id] = []

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
                    
        # Spam detection logic
        # Check if author_id exists in self.spam_messages and initialize if not
        if author_id not in self.spam_messages:
            self.spam_messages[author_id] = []

        # Retrieve messages_threshold and duration_threshold from thresholds dictionary
        if 'spam' in self.thresholds[guild_id]:
            spam_threshold = self.thresholds[guild_id]['spam']
            if isinstance(spam_threshold, dict):
                messages_threshold = spam_threshold.get('messages', 5)
                duration_threshold = spam_threshold.get('duration', 10)

                # Check if the number of messages exceeds the threshold
                if len(self.spam_messages[author_id]) >= messages_threshold:
                    # Check the time difference between the last message and the current message
                    current_time = message.created_at
                    last_message_time = self.spam_messages[author_id][-1]
                    time_difference = (current_time - last_message_time).seconds

                    if time_difference <= duration_threshold:
                        # Spam detected
                        # Delete previous spam messages of the user
                        async for prev_message in message.channel.history(limit=None):
                            if prev_message.author == message.author:
                                await prev_message.delete()
                        await self.add_spam_strike(message.author)
                    else:
                        # Reset spam messages list
                        self.spam_messages[author_id] = [current_time]
                else:
                    # Add message time to the list
                    self.spam_messages[author_id].append(message.created_at)
                    
                    # Notify the user about not being spam
                    embed = discord.Embed(title="Spam Detection",
                                        description="Your message was not detected as spam.",
                                        color=discord.Color.green())
                    await message.author.send(embed=embed)

        # Save spam messages to JSON file after each message
        self.save_spam_messages()

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
