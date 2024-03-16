import discord
from discord.ext import commands
from discord import client
import random
import asyncio
import os
import json

class Mods(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.muted_role_name = "Muted"  # Define muted_role_name here
        self.banned_words_db = {}  # Dictionary to store banned words for each guild
        # Load banned words and strikes databases from JSON files
        self.load_banned_words()

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

    # Save Banned Words to JSON file--------------------------------------------------
    def save_banned_words(self):
        with open('banned_words.json', 'w') as file:
            json.dump(self.banned_words_db, file, indent=4)

    class DurationConverter(commands.Converter):
        async def convert(self, ctx, argument):
            amount = argument[:-1]
            unit = argument[-1]
            if amount.isdigit() and unit in ['s', 'm', 'h', 'd']:
                return(int(amount), unit)
            raise commands.BadArgument(message='Not a valid duration')   
    
    # Clear Command--------------------------------------------------------------------
    @commands.command(aliases=['cl','purge'])
    @commands.has_permissions(manage_messages = True)
    async def clear(self, ctx, amount: int = None):
        if amount == 0:
            await ctx.send("🙄What made you type this!", delete_after=5)
            await ctx.channel.purge(limit = 2)
            print("Not specified")
        elif amount == None:
            await ctx.send("❗Please specify a number.")
            print("NO no. given")
        elif amount >= 1:
            await ctx.channel.purge(limit = amount+1)
            print(f'Cleared {amount} messages!')
        await ctx.send(f'✅ Cleared {amount} messages!', delete_after=5)

    # Mute Command------------------------------------------------------------------
    @commands.command(name='mute')
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, duration: DurationConverter):
        muted_role = discord.utils.get(ctx.guild.roles, name=self.muted_role_name)

        multiplier = {'s': 1, 'm': 60,'h': 3600,'d': 86400}
        amount, unit = duration
        
        if not muted_role:
            # Create the muted role if it doesn't exist
            muted_role = await ctx.guild.create_role(name=self.muted_role_name)
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)
                
        await member.add_roles(muted_role)
        myembed = discord.Embed(title="Moderation", description=f'{member} has been muted for {amount}{unit}.', color=0x00ffff)
        myembed.set_footer(text=f"Action taken by: {ctx.author.name}{ctx.author.discriminator}")
        await ctx.message.channel.send(embed=myembed)
        if duration is not None:
            await asyncio.sleep(amount * multiplier[unit])  # Convert to seconds
            await member.remove_roles(muted_role)
        else:
            myembed = discord.Embed(title="Moderation", description=f'{member} has been muted for 24h.', color=0x00ffff)
            myembed.set_footer(text=f"Action taken by: {ctx.author.name}{ctx.author.discriminator}")
            await ctx.message.channel.send(embed=myembed)
            await asyncio.sleep(24 * 60 * 60)  # for 24hr
            await member.remove_roles(muted_role)

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please specify a valid duration in minutes.")

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to manage roles.")

        else:
            await ctx.send("An error occurred while processing the command. Please try again later.")
    
    # Kick Command------------------------------------------------------------------
    @commands.command(name='kick', aliases=['k'])
    @commands.has_permissions(kick_members = True)
    async def kick(self, ctx, member: commands.MemberConverter, *,reason=None):
        await member.kick(reason=reason)
        myembed = discord.Embed(title="Moderation", description=f"{member} has been kicked.\nReason: {reason}", color=0x00ffff)
        myembed.set_footer(text=f"Action taken by: {ctx.author.name}{ctx.author.discriminator}")
        await ctx.message.channel.send(embed=myembed)

    # Ban Command-------------------------------------------------------------------
    @commands.command(name='ban')
    @commands.has_permissions(ban_members = True)
    async def ban(self, ctx, member : commands.MemberConverter, *,reason=None):
        await member.ban(reason=reason)
        myembed = discord.Embed(title="Moderation", description=f"{member} has been banned.\nReason: {reason}", color=0x00ffff)
        myembed.set_footer(text=f"Action taken by: {ctx.author.name}{ctx.author.discriminator}")
        await ctx.message.channel.send(embed=myembed)

    # Tempban Command---------------------------------------------------------------
    @commands.command(name='tempban')
    @commands.has_permissions(ban_members = True)
    async def tempban(self, ctx, member: commands.MemberConverter, duration: DurationConverter, *, reason=None):

        multiplier = {'s': 1, 'm': 60,'h': 3600,'d': 86400}
        amount, unit = duration
        
        await ctx.guild.ban(member, reason=reason)
        myembed = discord.Embed(title="Moderation", description=f'{member} has been banned for {amount}{unit}.\nReason: {reason}', color=0x00ffff)
        myembed.set_footer(text=f"Action taken by: {ctx.author.name}{ctx.author.discriminator}")
        await ctx.message.channel.send(embed=myembed)
        await asyncio.sleep(amount * multiplier[unit])
        await ctx.guild.unban(member)

    # Unban Command-----------------------------------------------------------------
    @commands.command(name='unban')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        banned_users = ctx.guild.bans()
        member_name, member_discriminator = member.split('#')
        
        async for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                myembed = discord.Embed(
                    title="Moderation",
                    description=f"{user} has been unbanned.",
                    color=0x00ffff
                )
                myembed.set_footer(text=f"Action taken by: {ctx.author.name}#{ctx.author.discriminator}")
                await ctx.send(embed=myembed)
                return
        
        # If the loop completes without finding a match, send an error message
        await ctx.send(f"User {member} was not found in the ban list.")
        
    # Slowmode---------------------------------------------------------------------------------------------------
    @commands.group(name='slowmode', aliases=['sm','slomo'] , invoke_without_command=True)
    async def slowmode(self, ctx):
        await ctx.send("Invalid slowmode command. Use `slowmode set <delay>`, `slowmode get`, or `slowmode reset`.")

    @slowmode.command(name='set')
    @commands.has_permissions(manage_messages=True)
    async def set_slowmode(self, ctx, delay: int):
        await ctx.channel.edit(slowmode_delay=delay)
        await ctx.send(f'Slowmode set to {delay} seconds for this channel.')

    @slowmode.command(name='get')
    @commands.has_permissions(manage_messages=True)
    async def get_slowmode(self, ctx):
        if ctx.channel.slowmode_delay:
            await ctx.send(f'The slowmode delay for this channel is {ctx.channel.slowmode_delay} seconds.')
        else:
            await ctx.send('There is no slowmode set for this channel.')

    @slowmode.command(name='reset')
    @commands.has_permissions(manage_messages=True)
    async def reset_slowmode(self, ctx):
        await ctx.channel.edit(slowmode_delay=0)
        await ctx.send('Slowmode reset for this channel.')
        
    # Banned Words--------------------------------------------------------------------------    
    @commands.group(name='bannedwords', aliases = ['bw','bannedw','wordban'], invoke_without_command=True)
    async def banned_words(self, ctx):
        embed = discord.Embed(title="Banned Words Command",
                              description="Invalid banned words command. Use the following subcommands:",
                              color=discord.Color.red())
        embed.add_field(name="Add Banned Word",
                        value="`bannedwords add <word>`: Add a word to the list of banned words.",
                        inline=False)
        embed.add_field(name="Get Banned Words",
                        value="`bannedwords get`: Get the list of banned words for this server.",
                        inline=False)
        embed.add_field(name="Remove Banned Word",
                        value="`bannedwords remove <word>`: Remove a word from the list of banned words.",
                        inline=False)
        await ctx.send(embed=embed)

    @banned_words.command(name='add')
    @commands.has_permissions(manage_guild=True)
    async def add_banned_word(self, ctx, *words: str):
        guild_id = str(ctx.guild.id)
        if guild_id not in self.banned_words_db:
            self.banned_words_db[guild_id] = []

        added_words = []
        already_added_words = []

        for word in words:
            if word.lower() not in self.banned_words_db[guild_id]:
                self.banned_words_db[guild_id].append(word.lower())
                added_words.append(word)
            else:
                already_added_words.append(word)

        if added_words:
            embed = discord.Embed(title="Banned Words Command",
                                description=f'Added words to the list of banned words: {", ".join(added_words)}',
                                color=discord.Color.green())
        else:
            embed = discord.Embed(title="Banned Words Command",
                                description='No new words added to the list of banned words.',
                                color=discord.Color.red())
        if already_added_words:
            embed.add_field(name="Already in List", value=f"{', '.join(already_added_words)} is already in the list of banned words.", inline=False)

        await ctx.send(embed=embed)
        self.save_banned_words()

    @banned_words.command(name='remove')
    @commands.has_permissions(manage_guild=True)
    async def remove_banned_word(self, ctx, *words: str):
        guild_id = str(ctx.guild.id)
        if guild_id in self.banned_words_db:
            removed_words = []
            not_in_list_words = []

            for word in words:
                if word.lower() in self.banned_words_db[guild_id]:
                    self.banned_words_db[guild_id].remove(word.lower())
                    removed_words.append(word)
                else:
                    not_in_list_words.append(word)

            if removed_words:
                embed = discord.Embed(title="Banned Words Command",
                                    description=f'Removed words from the list of banned words: {", ".join(removed_words)}',
                                    color=discord.Color.green())
            else:
                embed = discord.Embed(title="Banned Words Command",
                                    description='No words removed from the list of banned words.',
                                    color=discord.Color.red())
            if not_in_list_words:
                embed.add_field(name="Not in List", value=f"{', '.join(not_in_list_words)} is not in the list of banned words.", inline=False)

        else:
            embed = discord.Embed(title="Banned Words Command",
                                description='There are no banned words for this server.',
                                color=discord.Color.red())

        await ctx.send(embed=embed)
        self.save_banned_words()


    @banned_words.command(name='get')
    @commands.has_permissions(manage_guild=True)
    async def get_banned_words(self, ctx):
        guild_id = str(ctx.guild.id)
        if guild_id in self.banned_words_db:
            banned_words = ", ".join(self.banned_words_db[guild_id])
            embed = discord.Embed(title="Banned Words Command",
                                  description=f'Banned words for this server: {banned_words}',
                                  color=discord.Color.blue())
        else:
            embed = discord.Embed(title="Banned Words Command",
                                  description='There are no banned words for this server.',
                                  color=discord.Color.blue())
        await ctx.send(embed=embed)
        
async def setup(client):
    await client.add_cog(Mods(client))