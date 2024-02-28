from re import A
import discord
from discord import client, Embed
from discord import channel
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType
import asyncio
from discord.ext.commands import BadArgument
from typing import Optional
from random import choice, randint
from aiohttp import request
import random

class Cmd(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Ping Command----------------------------------------------------
    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.channel.purge(limit = 1)
        await ctx.send(f'🏓Pong! {round(self.client.latency * 1000)}ms', delete_after=10)
        

    # Version of Bot......................................................
    @commands.command(name='version')
    async def version(self, context):
        await context.message.delete()
        myembed = discord.Embed(title="Current Version", description="The bot is currently in Trial Phase", color=0x00ffff)
        myembed.add_field(name="Version Code:", value="1.0", inline=False)
        myembed.add_field(name="Date Released:", value="October 10th, 2021", inline=False)
        myembed.set_footer(text="Information may change in the future")
        myembed.set_author(name="Story", icon_url=context.bot.user.avatar.url)  # Use bot's user avatar.url
        await context.send(embed=myembed)


    # Q&A--------------------------------------------------------------------------
    @commands.command(name='ques')
    async def _8ball(self, ctx, *, question: str = None):
        responses = ['It is certain.',
                    'It is decidedly so.',
                    'Without a doubt.',
                    'Yes definitely.',
                    'You may rely on it.',
                    'As I see it, yes.',
                    'Most likely.',
                    'Outlook good.',
                    'Yes.',
                    'Signs point to yes.',
                    'Reply hazy, try again.',
                    'Ask again later.',
                    'Better not tell you now.',
                    'Cannot predict now.',
                    'Concentrate and ask again.',
                    'Dont count on it.',
                    'My reply is no.',
                    'My sources say no.',
                    'Outlook not so good.'
                    ,'Very doubtful.']
        if question == None:
            await ctx.send("Ask any Yes/No question and I will Answer.")
            print('Please emter a question')
        else:
            await ctx.send(f'{random.choice(responses)}')

    # Say--------------------------------------------------------------------------
    @commands.command(name="say", aliases=["echo"])
    async def echo_message(self,ctx, *, message):
        await ctx.message.delete()
        await ctx.send(message)

async def setup(client):
    await client.add_cog(Cmd(client))