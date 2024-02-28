import discord
from discord.ext import commands
from discord import client
import random
import asyncio

class Mods(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.spam_records = {}  # Dictionary to track spam records
        
    # Auto Moderation Command -----------------------------------------------------
    async def process_spam(self, member, ctx):
        if member.id not in self.spam_records:
            self.spam_records[member.id] = {"count": 1, "time": ctx.message.created_at}
        else:
            record = self.spam_records[member.id]
            current_time = ctx.message.created_at
            time_difference = (current_time - record["time"]).seconds

            if time_difference < 10:  # Customize this threshold as needed
                record["count"] += 1
                if record["count"] >= 5:
                    del self.spam_records[member.id]
                    await self.temp_mute(member)
                else:
                    record["time"] = current_time
            else:
                record["count"] = 1
                record["time"] = current_time

    async def temp_mute(self, member):
        mute_role = discord.utils.get(member.guild.roles, name="Muted")  # Replace with your mute role's name
        if not mute_role:
            # Create the mute role if it doesn't exist
            mute_role = await member.guild.create_role(name="Muted")

            # Apply permissions to the mute role (e.g., send no messages, can't speak)
            for channel in member.guild.channels:
                await channel.set_permissions(mute_role, send_messages=False, speak=False)

        await member.add_roles(mute_role)
        await asyncio.sleep(1800)  # 30 minutes in seconds
        await member.remove_roles(mute_role)

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
    async def mute(self, ctx, member: discord.Member, duration: int = None):
        muted_role = discord.utils.get(ctx.guild.roles, name=self.muted_role_name)

        if not muted_role:
            # Create the muted role if it doesn't exist
            muted_role = await ctx.guild.create_role(name=self.muted_role_name)
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False)

        await member.add_roles(muted_role)
        
        if duration is not None:
            await asyncio.sleep(duration * 60)  # Convert to seconds
            await member.remove_roles(muted_role)
        
        await ctx.send(f"{member.mention} has been muted{' temporarily' if duration else ''}.")
    
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
    class DurationConverter(commands.Converter):
        async def convert(self, ctx, argument):
            amount = argument[:-1]
            unit = argument[-1]
            if amount.isdigit() and unit in ['s', 'm', 'h', 'd']:
                return(int(amount), unit)
            raise commands.BadArgument(message='Not a valid duration')

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



async def setup(client):
    await client.add_cog(Mods(client))