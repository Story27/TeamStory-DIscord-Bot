import discord
from discord.ext import commands
import asyncio

# Import the Strikes cog class from the Strikes module
from .strikes import Strikes

class AutoModSetup(commands.Cog):
    def __init__(self, client, strikes_cog):
        self.client = client
        self.strikes_cog = strikes_cog  # Reference to Strikes cog

    @commands.command(name='automod', aliases=['automod_setup'])
    @commands.has_permissions(manage_messages=True)
    async def automod_setup(self, ctx):
        if not self.strikes_cog:
            return await ctx.send("Strikes cog is not loaded. Please make sure Strikes cog is loaded.")

        guild_id = str(ctx.guild.id)
        thresholds = self.strikes_cog.thresholds.get(guild_id, {})
        
        embed = discord.Embed(title="AutoMod Setup", description="Current AutoMod Settings:", color=discord.Color.blue())

        for action, data in thresholds.items():
            if action == 'ban':
                embed.add_field(name=f"{action.capitalize()} Threshold",
                                value=f"Strikes: {data.get('strikes', 'N/A')}",
                                inline=False)
            elif action == 'spam':
                embed.add_field(name=f"{action.capitalize()} Threshold",
                                value=f"Messages: {data.get('messages', 'N/A')}\nDuration: {data.get('duration', 'N/A')} seconds",
                                inline=False)
            else:
                embed.add_field(name=f"{action.capitalize()} Threshold",
                                value=f"Strikes: {data.get('strikes', 'N/A')}\nDuration: {data.get('duration', 'N/A')} seconds",
                                inline=False)


        embed.set_footer(text="React with ✏️ to customize settings or ❌ to cancel.")

        message = await ctx.send(embed=embed)
        await message.add_reaction('✏️')
        await message.add_reaction('❌')

        def reaction_check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✏️', '❌'] and reaction.message.id == message.id

        try:
            reaction, _ = await self.client.wait_for('reaction_add', timeout=60.0, check=reaction_check)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            return

        if str(reaction.emoji) == '❌':
            await message.clear_reactions()
            return await message.edit(content="AutoMod setup cancelled.")

        await self.customize_settings(ctx, message)

    async def customize_settings(self, ctx, message):
        guild_id = str(ctx.guild.id)
        thresholds = self.strikes_cog.thresholds.get(guild_id, {})
        try:
            while True:
                await message.edit(content="Please specify the action you want to customize (tempmute, mute, tempban, ban, spam):")
                action_msg = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                action = action_msg.content.lower()
                await ctx.channel.purge(limit=1)

                if action not in thresholds:
                    await message.edit(content=f"Invalid action '{action}'. Please try again.")
                    continue
                if action!='spam':
                    await message.edit(content=f"Please specify the new number of strikes for {action.capitalize()}:")
                    strikes_msg = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                    strikes = int(strikes_msg.content)
                    await ctx.channel.purge(limit=1)
                    await message.edit(content=f"Please specify the new duration (in seconds) for {action.capitalize()}:")
                    duration_msg = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                    duration = int(duration_msg.content)
                    await ctx.channel.purge(limit=1)

                if action == 'spam':
                    await message.edit(content=f"Please specify the no. of messages for {action.capitalize()}:")
                    msg_msg = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                    msg = int(msg_msg.content)
                    await ctx.channel.purge(limit=1)
                    await message.edit(content=f"Please specify the new duration (in seconds) for {action.capitalize()}:")
                    duration_msg = await self.client.wait_for('message', check=lambda m: m.author == ctx.author, timeout=60.0)
                    duration = int(duration_msg.content)
                    await ctx.channel.purge(limit=1)
                    thresholds[action]['messages'] = msg
                else:
                    thresholds[action]['strikes'] = strikes
                if action != 'ban':
                    thresholds[action]['duration'] = duration
                self.strikes_cog.save_server_thresholds(guild_id)

                # Remove the embedded message temporarily
                await message.clear_reactions()
                await message.delete()

                # Update embedded message with new settings
                updated_embed = discord.Embed(title="AutoMod Setup", description="Current AutoMod Settings:", color=discord.Color.blue())
                for action, data in thresholds.items():
                    if action == 'ban':
                        updated_embed.add_field(name=f"{action.capitalize()} Threshold",
                                                value=f"Strikes: {data['strikes']}",
                                                inline=False)
                    elif action == 'spam':
                        updated_embed.add_field(name=f"{action.capitalize()} Threshold",
                                        value=f"Messages: {data.get('messages', 'N/A')}\nDuration: {data.get('duration', 'N/A')} seconds",
                                        inline=False)
                    else:
                        updated_embed.add_field(name=f"{action.capitalize()} Threshold",
                                                value=f"Strikes: {data['strikes']}\nDuration: {data.get('duration', 'N/A')} seconds",
                                                inline=False)
                updated_embed.set_footer(text="React with ✏️ to customize settings or ❌ to cancel.")

                # Send the updated embedded message
                message = await ctx.send(embed=updated_embed)

                # Add reactions for further interaction
                await message.add_reaction('✏️')
                await message.add_reaction('❌')

                # Wait for user reaction
                def reaction_check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ['✏️', '❌'] and reaction.message.id == message.id
                reaction, _ = await self.client.wait_for('reaction_add', check=reaction_check, timeout=60.0)

                # Handle user reaction
                if str(reaction.emoji) == '❌':
                    await message.edit(content="AutoMod setup completed Successfully.")
                    break
                else:
                    await message.clear_reactions()
                    continue
        except asyncio.TimeoutError:
            await message.edit(content="AutoMod setup timed out.")
        finally:
            await message.clear_reactions()



# Setup function
async def setup(client):
    strikes_cog = None
    for cog in client.cogs.values():
        if isinstance(cog, Strikes):
            strikes_cog = cog
            break

    if not strikes_cog:
        print("Strikes cog is not loaded. Please make sure Strikes cog is loaded.")
        return

    await client.add_cog(AutoModSetup(client, strikes_cog))
