# Import Discord Package
import asyncio
import random
import json
import os
from logging import fatal
from re import purge
from sys import prefix, pycache_prefix
import discord
from itertools import cycle
from discord import user
from discord import activity
from discord import message
from discord import colour
from discord.channel import VoiceChannel
from discord.client import Client
from discord.colour import Color
from discord.embeds import Embed
from discord.ext import commands, tasks
from discord.ext.commands import bot, CommandError
from discord.ext.commands.core import command
from random import choice
import sqlite3
import wavelink as wavelink
from wavelink.ext import spotify
from yarl import URL
import youtube_dl
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Prefix
prefixes = {}

def get_prefix(client, message):
    try:
        return prefixes[str(message.guild.id)]
    except KeyError:
        return ">>"

# Client
intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True  # Make sure voice_states are enabled in intents
client = commands.Bot(command_prefix = get_prefix, intents=intents)
client.remove_command("help")

@client.command()
@commands.has_permissions(administrator=True)
async def load(ctx, extension: str = None):
    if extension is None:
        await ctx.send('Please mention the Extension!')
    else:
        await client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Loaded {extension}.')
    
@client.tree.command(name='load', description="Loads the extension")
async def load(interaction: discord.interactions, extension:str=None):
    if extension is None:
        await interaction.response.send_message('Please mention the Extension!')
    else:
        await client.load_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'Loaded {extension}.')

@client.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension: str = None):
    if extension is None:
        await ctx.send('Please mention the Extension!')
    else:
        await client.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Unloaded {extension}.')
        
@client.tree.command(name='unload', description="Unloads the extension")
@commands.has_permissions(administrator=True)
async def load(interaction: discord.interactions, extension:str=None):
    if extension is None:
        await interaction.response.send_message('Please mention the Extension!')
    else:
        await client.unload_extension(f'cogs.{extension}')
        await interaction.response.send_message(f'Unloaded {extension}.')

@client.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension: str = None):
    if extension is None:
        await ctx.send('Please mention the Extension!')
    else:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Reloaded {extension}.')

@client.tree.command(name='shutdown', description="Shuts down the bot")
@commands.has_permissions(administrator=True)
async def shutdown(interaction: discord.interactions):
    await interaction.response.send_message(content="Bye Byeeee!!! :)")
    await client.close()

@client.command(name='shutdown', aliases=['close','stop','soja'])
async def shutdown(ctx):
    await ctx.send("Bye Byeeee!!! :)")
    await client.close()

# Load all extensions when the bot starts
async def load_cogs():
    cog_files = sorted(os.listdir('./cogs'), reverse=True)
    for filename in cog_files:
        if filename.endswith('.py'):
            try:
                await client.load_extension(f'cogs.{filename[:-3]}')
                print(f'Loaded {filename[:-3]} extension.')
            except commands.ExtensionError as e:
                print(f"Failed to load extension {filename}: {e}")


@client.event
async def on_guild_join(guild):
    with open('prefixes.json', 'r') as f:
        global prefixes
        prefixes = json.load(f)
    prefixes[str(guild.id)] = '>>'
    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

@client.event
async def on_guild_remove(guild):
    with open('prefixes.json', 'r') as f:
        global prefixes
        prefixes = json.load(f)

    prefixes.pop(str(guild.id))

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

@client.command(name='prefix')
async def changeprefix(ctx, prefix):
    with open('prefixes.json', 'r') as f:
        global prefixes
        prefixes = json.load(f)

    prefixes[str(ctx.guild.id)] = prefix

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

    await ctx.send(f'Prefix changed to: {prefix}')

# Online Checking...
@client.event
async def on_ready():
    with open('prefixes.json', 'r') as f:
        global prefixes
        prefixes = json.load(f)

    await load_cogs()
    change_status.start()
    synced = await client.tree.sync()
    print("Slash CMDs Synced " + str(len(synced)) + " Commands")
    print('Team Story is online!')
    # DO STUFF....
    general_channel = client.get_channel(855302146467299330)
    await general_channel.send('Who woke me up!!', delete_after=10)


############################################################################################################################
############################################################################################################################################
#####################################################################################################################################


# Help Command................................................
@client.group(invoke_without_command=True)
async def help(ctx):
    prefix = get_prefix(client, ctx.message) # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Command Help",
                       description="Below is a list of available commands. "
                                   "Use `{prefix}help <command>` for extended information on a command."
                                   "\n\n**Moderation:**\n"
                                   "`{prefix}kick`: Kicks a member from the guild\n"
                                   "`{prefix}ban`: Bans a member from the guild\n"
                                   "`{prefix}unban`: Unbans a member from the guild\n"
                                   "`{prefix}tempban`: Temporarily bans a member from the guild\n"
                                   "`{prefix}clear`: Clears a specified number of messages from the guild\n"
                                   "`{prefix}wordban`: Bans a specified word from being used in the guild\n"
                                   "`{prefix}slowmode`: Sets a slow mode in the current channel\n"
                                   "`{prefix}automod`: Enables or configures auto moderation settings\n"
                                   "`{prefix}strikes`: Manages strikes for members\n"
                                   "\n**Info:**\n"
                                   "`{prefix}userinfo`: Gives information about a user\n"
                                   "\n**Fun:**\n"
                                   "`{prefix}ques`: Ask any Yes/No question\n"
                                   "`{prefix}version`: Tells you the current version of the bot\n"
                                   "`{prefix}ping`: Tells the bot's ping"
                       .format(prefix=prefix),
                       color=0x00ffff)

    await ctx.send(embed=em)

@help.command(name='kick')
async def kick_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Kick Command",
                       description="Kicks a member from the guild",
                       color=ctx.author.colour)
    em.add_field(name="**Alias**", value="`kick`, `k`", inline=False)
    em.add_field(name="**Syntax**", value=f"`{prefix}kick <member> [reason]`", inline=False)
    await ctx.send(embed=em)


@help.command(name='ban')
async def ban_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Ban Command",
                       description="Bans a member from the guild",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}ban <member> [reason]`", inline=False)
    await ctx.send(embed=em)


@help.command(name='tempban')
async def tempban_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Tempban Command",
                       description="Bans a member temporarily for a specified time from the guild",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}tempban <member> (time)[s/m/h/d] [reason]`", inline=False)
    await ctx.send(embed=em)


@help.command(name='unban')
async def unban_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Unban Command",
                       description="Unbans a member from the guild",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}unban <Name#0000>`", inline=False)
    await ctx.send(embed=em)


@help.command(name='clear')
async def clear_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Clear Command",
                       description="Clears a specified number of messages from the guild",
                       color=ctx.author.colour)
    em.add_field(name="**Alias**", value="`clear`, `cl`, `purge`", inline=False)
    em.add_field(name="**Syntax**", value=f"`{prefix}[clear | cl | purge] [amount]`", inline=False)
    await ctx.send(embed=em)


@help.command(name='userinfo', aliases=["memberinfo", "ui", "mi"])
async def userinfo_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="User Information Command",
                       description="Gives information of the person tagged or the member using the command.",
                       color=ctx.author.colour)
    em.add_field(name="**Alias**", value="`userinfo`, `memberinfo`, `ui`, `mi`", inline=False)
    em.add_field(name="**Syntax**", value=f"`{prefix}[userinfo | memberinfo | ui | mi] <member>` (optional)", inline=False)
    await ctx.send(embed=em)


@help.command(name='ques')
async def ques_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Question Command",
                       description="Ask any Yes/No question to me and I will answer them.",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}ques [question]`", inline=False)
    await ctx.send(embed=em)


@help.command(name='version')
async def version_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Version Command",
                       description="Tells you the current version of the bot",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}version`", inline=False)
    await ctx.send(embed=em)


@help.command(name='ping')
async def ping_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Ping Command",
                       description="Tells you the bot's latency.",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}ping`", inline=False)
    await ctx.send(embed=em)

@help.command(name= 'music')
async def music(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]

    em = discord.Embed(title = "Music", description = "All the commands needed for Listening to Music can be found here.", color=ctx.author.colour)
    em.add_field(name = f"**Type {pre}music**")
    await ctx.send(embed = em)  
    
@help.command(name = 'say')
async def Say(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Say", description = "The bot repeats what you want the bot to say.", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}say [message]', inline=False)
    await ctx.send(embed = em) 
    
@help.command(name='strikes')
async def strikes_help(ctx):
    em = discord.Embed(title="Strikes Command",
                       description="Manage strikes for users.",
                       color=0x00ffff)
    em.add_field(name="Check Strikes",
                 value="`strikes check <user>`: Check the number of strikes for a user.",
                 inline=False)
    em.add_field(name="Add Strikes",
                 value="`strikes add <user> <amount>`: Add strikes to a user.",
                 inline=False)
    em.add_field(name="Remove Strikes",
                 value="`strikes remove <user> <amount>`: Remove strikes from a user.",
                 inline=False)
    em.add_field(name="Set Thresholds",
                 value="`strikes set <action> <threshold>`: Set the threshold for an action (tempmute, mute, tempban, ban).",
                 inline=False)
    await ctx.send(embed=em)

@help.command(name='automod')
async def automod_help(ctx):
    em = discord.Embed(title="AutoMod Setup Command",
                       description="Configure AutoMod settings.",
                       color=0x00ffff)
    em.add_field(name="Setup",
                 value="`automod setup`: Setup AutoMod settings.",
                 inline=False)
    await ctx.send(embed=em)

@help.command(name='wordban')
async def wordban_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Word Ban Command",
                       description="Bans a specified word from being used in the guild",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}wordban <word>`", inline=False)
    await ctx.send(embed=em)


@help.command(name='slowmode', aliases = ['slomo','sm'])
async def slowmode_help(ctx):
    prefix = get_prefix(client, ctx.message)  # You need to define a function to get the prefix for the guild

    em = discord.Embed(title="Slow Mode Command",
                       description="Sets a slow mode in the current channel.",
                       color=ctx.author.colour)
    em.add_field(name="**Syntax**", value=f"`{prefix}slowmode <time>`", inline=False)
    await ctx.send(embed=em)


# Status
status = cycle(["GTA X : Founder's Edition", "Story's Video", "My favourite Game", "why am I playing"])
@tasks.loop(seconds=10)
async def change_status():
     await client.change_presence(activity=discord.Game(next(status))) 
     
# Banned words------------------------------------------------------------------------
client.event
async def on_message(msg):
    if msg.content == "hi":
        await msg.delete()
        await msg.channel.send("Don't send that again otherwise there will be actions!")
     

# Run the client on the server
Token = os.getenv('TOKEN')
client.run(Token)