from datetime import datetime
from typing import Optional
import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo", aliases=["memberinfo", "ui", "mi"])
    async def user_info(self, ctx, target: Optional[discord.Member]):
        target = target or ctx.author

        if isinstance(target, discord.Member):
            user = target
        else:
            user = target

        embed = discord.Embed(title="User information", color=0x00ffff, timestamp=datetime.utcnow())
        embed.set_thumbnail(url=user.avatar.url)

        fields = [
            ("Name", str(user), True),
            ("ID", user.id, True),
            ("Bot?", user.bot, True),
            ("Top role", user.top_role.mention, True),
            ("Status", str(user.status).title(), True),
            (
                "Activity",
                f"{str(user.activity.type).split('.')[-1].title()} {user.activity.name}" if user.activity else "N/A",
                True,
            ),
            ("Created at", user.created_at.strftime("%d/%m/%Y %H:%M:%S"), True),
            ("Joined at", user.joined_at.strftime("%d/%m/%Y %H:%M:%S") if isinstance(user, discord.Member) else "N/A", True),
            ("Boosted", bool(user.premium_since), True),
        ]

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
