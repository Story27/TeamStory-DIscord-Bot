from datetime import datetime
import discord
from discord.ext import commands
from discord import Embed
from discord.ext.commands import Cog
from discord.ext.commands import command


class Log(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
	
	@commands.Cog.listener()
	async def on_user_update(self, before, after):
		ch_id = 855302146467299331
		if before.name != after.name:
			embed = Embed(title="Username change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.name, False),
					  ("After", after.name, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await self.bot.get_channel(ch_id).send(embed=embed)

		if before.discriminator != after.discriminator:
			embed = Embed(title="Discriminator change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.discriminator, False),
					  ("After", after.discriminator, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await self.bot.get_channel(ch_id).send(embed=embed)

		if before.avatar_url != after.avatar_url:
			embed = Embed(title="Avatar change",
						  description="New image is below, old to the right.",
						  colour=self.log_channel.guild.get_member(after.id).colour,
						  timestamp=datetime.utcnow())

			embed.set_thumbnail(url=before.avatar_url)
			embed.set_image(url=after.avatar_url)

			await self.bot.get_channel(ch_id).send(embed=embed)

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		ch_id = 855302146467299331
		if before.display_name != after.display_name:
			embed = Embed(title="Nickname change",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", before.display_name, False),
					  ("After", after.display_name, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await self.bot.get_channel(ch_id).send(embed=embed)

		elif before.roles != after.roles:
			embed = Embed(title="Role updates",
						  colour=after.colour,
						  timestamp=datetime.utcnow())

			fields = [("Before", ", ".join([r.mention for r in before.roles]), False),
					  ("After", ", ".join([r.mention for r in after.roles]), False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await self.bot.get_channel(ch_id).send(embed=embed)

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		ch_id = 855302146467299331
		if not after.author.bot:
			if before.content != after.content:
				embed = Embed(title="Message edit",
							  description=f"Edit by {after.author.display_name}.",
							  colour=after.author.colour,
							  timestamp=datetime.utcnow())

				fields = [("Before", before.content, False),
						  ("After", after.content, False)]

				for name, value, inline in fields:
					embed.add_field(name=name, value=value, inline=inline)

				await self.bot.get_channel(ch_id).send(embed=embed)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		ch_id = 855302146467299331
		if not message.author.bot:
			embed = Embed(title="Message deletion",
						  description=f"Action by {message.author.display_name}.",
						  colour=message.author.colour,
						  timestamp=datetime.utcnow())

			fields = [("Content", message.content, False)]

			for name, value, inline in fields:
				embed.add_field(name=name, value=value, inline=inline)

			await self.bot.get_channel(ch_id).send(embed=embed)


async def setup(bot):
	await bot.add_cog(Log(bot))