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
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Loaded {extension}.')

@client.command()
@commands.has_permissions(administrator=True)
async def unload(ctx, extension: str = None):
    if extension is None:
        await ctx.send('Please mention the Extension!')
    else:
        client.unload_extension(f'cogs.{extension}')
        await ctx.send(f'Unloaded {extension}.')

@client.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, extension: str = None):
    if extension is None:
        await ctx.send('Please mention the Extension!')
    else:
        client.unload_extension(f'cogs.{extension}')
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f'Reloaded {extension}.')

# Load all extensions when the bot starts
async def load_cogs():
    for filename in os.listdir('./cogs'):
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
    em = discord.Embed(title = "help", description = "use >>help <command> for extended information on a command.", color=0x00ffff)

    em.add_field(name = "Moderation", value = "1. Kick\n2. Ban\n3. Unban\n4. Tempban\n5. Clear", inline=False)
    em.add_field(name = "Info", value = '1. Userinfo', inline=False)
    em.add_field(name = "Fun", value = '1. Ques\n2. Version\n3. Ping', inline=False)

    await ctx.send(embed = em)

@help.command(name= 'kick')
async def Kick(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]

    em = discord.Embed(title = "Kick", description = "Kicks a member from the guild", color=ctx.author.colour)
    em.add_field(name = "**Alias**", value = "1. kick\n2. k", inline=False)
    em.add_field(name="**Syntax**", value=f"{pre}kick <member> [reason]", inline=False)
    await ctx.send(embed = em)  

@help.command(name = 'ban')
async def Ban(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Ban", description = "Bans a member from  the guild", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}ban <member> [reason]', inline=False)
    await ctx.send(embed = em) 

@help.command(name = 'tempban')
async def Ban(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Tempban", description = "Bans a member tmperorily for specified time from the guild", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}ban <member> (time)[s/m/h/d] [reason]', inline=False)
    await ctx.send(embed = em) 

@help.command(name = 'unban')
async def Unban(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Unban", description = "Unbans a member from  the guild", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}unban <Name#0000>', inline=False)
    await ctx.send(embed = em) 

@help.command(name = 'clear')
async def Clear(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Clear", description = "Clears specified number of messages from  the guild", color=ctx.author.colour)
    em.add_field(name = "**Alias**", value = "1. clear\n2. cl\n3. purge", inline=False)
    em.add_field(name = "**Syntax**", value = f"{pre}[clear | cl | purge] [amount]", inline=False)
    await ctx.send(embed = em)

@help.command(name = 'ques')
async def Ques(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Ques", description = "Ask any Yes/No question to me and I will answer them.", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}ques [question]', inline=False)
    await ctx.send(embed = em) 

@help.command(name = 'version')
async def Version(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Version", description = "Tells you the current version of the bot", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}version', inline=False)
    await ctx.send(embed = em) 

@help.command(name = 'ping')
async def Ping(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "Ping", description = "Tells the bot's ping", color=ctx.author.colour)
    em.add_field(name = "**Syntax**", value = f'{pre}ping', inline=False)
    await ctx.send(embed = em) 

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
    
@help.command(name = 'userinfo', aliases=["memberinfo", "ui", "mi"])
async def Clear(ctx):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    pre = prefixes[str(ctx.guild.id)]    
    em = discord.Embed(title = "User Inforation", description = "Gives information of the person tagged or the member using the command.", color=ctx.author.colour)
    em.add_field(name = "**Alias**", value = "1. memberinfo\n2. ui\n3. mi", inline=False)
    em.add_field(name = "**Syntax**", value = f"{pre}[userinfo | memberinfo | ui | mi] <member>(optional)", inline=False)
    await ctx.send(embed = em)


# Status
status = cycle(["GTA X : Founder's Edition", "Story's Video", "My favourite Game", "why am I playing"])
@tasks.loop(seconds=10)
async def change_status():
     await client.change_presence(activity=discord.Game(next(status))) 
     

# Run the client on the server
client.run('OTAzMjE1NTQyNjY2Njg2NTE1.GGbDJN.FkHlbDlo4zF1q9jhd8uxQoqxYP8XOflbLLyXeQ')