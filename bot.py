from datetime import datetime, timezone
import discord
from discord.ext import commands

# --- CONFIGURATION ---
import os

TOKEN = os.getenv("MTU0NDc0Mjc4NzUyMDM5NzQ2Mg.GuMfr2.aUi9TfB4Zvu7FVrnC2Kw3Edlieops844WKdfVw")  # Replace with your bot token
LOG_CHANNEL_ID = 1470132852141195441  # Replace with your staff/logs channel ID
MIN_ACCOUNT_AGE_DAYS = 7  # Minimum account age required in days

# Custom Blacklist (Add User IDs as integers)
BLACKLISTED_USER_IDS = {
    123456789012345678,
    987654321098765432,
}

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.members = True  # Required to detect when new members join

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Server Guard online as {bot.user.name} ({bot.user.id})")


@bot.event
async def on_member_join(member: discord.Member):
    log_channel = member.guild.get_channel(LOG_CHANNEL_ID)

    # 1. Check Custom Blacklist
    if member.id in BLACKLISTED_USER_IDS:
        reason = "User ID is on the server security blacklist."
        await kick_and_log(member, reason, log_channel)
        return

    # 2. Check Account Age
    now = datetime.now(timezone.utc)
    account_age = now - member.created_at
    account_age_days = account_age.days

    if account_age_days < MIN_ACCOUNT_AGE_DAYS:
        reason = f"Account is too new ({account_age_days} days old). Minimum required: {MIN_ACCOUNT_AGE_DAYS} days."
        await kick_and_log(member, reason, log_channel)
        return


async def kick_and_log(
    member: discord.Member, reason: str, log_channel: discord.TextChannel
):
    # Try sending a DM to the user before kicking
    try:
        await member.send(
            f"You were automatically kicked from **{member.guild.name}**.\n**Reason:** {reason}"
        )
    except discord.Forbidden:
        pass  # User has DMs closed

    # Kick the user
    try:
        await member.kick(reason=f"[Server Guard] {reason}")
    except discord.Forbidden:
        if log_channel:
            await log_channel.send(
                f"⚠️ **Failed to kick {member.mention}**: Bot lacks `Kick Members` permission or user has a higher role."
            )
        return

    # Send log entry
    if log_channel:
        embed = discord.Embed(
            title="🛡️ Anti-Alt Action Executed",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.add_field(
            name="User", value=f"{member.name} (`{member.id}`)", inline=False
        )
        embed.add_field(
            name="Account Created",
            value=f"<t:{int(member.created_at.timestamp())}:R>",
            inline=True,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)

        await log_channel.send(embed=embed)


# --- COMMANDS TO MANAGE BLACKLIST DYNAMICALLY ---
@bot.command(name="blacklist")
@commands.has_permissions(administrator=True)
async def add_blacklist(ctx, user_id: int):
    """Add a user ID to the blacklist."""
    BLACKLISTED_USER_IDS.add(user_id)
    await ctx.send(f"✅ Added user ID `{user_id}` to the blacklist.")


@bot.command(name="unblacklist")
@commands.has_permissions(administrator=True)
async def remove_blacklist(ctx, user_id: int):
    """Remove a user ID from the blacklist."""
    BLACKLISTED_USER_IDS.discard(user_id)
    await ctx.send(f"✅ Removed user ID `{user_id}` from the blacklist.")


bot.run(TOKEN)