import discord
from discord.ext import commands

# ---- CONFIG ----

# Roles that are allowed to run these commands (put your reviewer/mod roles here)
ALLOWED_ROLE_IDS = {
    1472717671425380433,
    1475118051253813501
}

# (Optional) allow specific users regardless of roles (can be empty)
ALLOWED_USER_IDS = {
    1102884420207255653,
    1156180438977617990
}

# Announcement channel
POST_CHANNEL_ID = 1472920155968508096

# Roles to assign
TRIAL_ROLE_ID = 1472881459864801469  # Trial Member
TEAM_ROLE_ID  = 1472725905074950226  # Team Member


class ThreadActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_allowed_member(self, member: discord.Member) -> bool:
        """Allowed if user is in ALLOWED_USER_IDS OR has any role in ALLOWED_ROLE_IDS."""
        if member.id in ALLOWED_USER_IDS:
            return True
        return any(role.id in ALLOWED_ROLE_IDS for role in getattr(member, "roles", []))

    async def _get_text_channel(self, guild: discord.Guild, channel_id: int):
        ch = guild.get_channel(channel_id)
        if ch is not None:
            return ch
        try:
            return await guild.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def _process_thread(
        self,
        ctx: commands.Context,
        role_id: int,
        accepted_label: str,
    ):
        # ---- 1) Must be run inside a thread (this check happens FIRST, always) ----
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.reply("You really thought you could do that, imagine...", delete_after=5)
            return

        thread: discord.Thread = ctx.channel
        guild = ctx.guild
        if guild is None:
            return  # should not happen in normal use

        # ---- 2) Permission check (allowed roles/users) ----
        # ctx.author is usually a Member in guild contexts; still guard just in case.
        author = ctx.author
        if not isinstance(author, discord.Member):
            try:
                author = await guild.fetch_member(ctx.author.id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                await thread.send("Could not resolve command author.")
                return

        if not self._is_allowed_member(author):
            await thread.send("❌ You are not allowed to use this command.")
            return

        # ---- 3) Resolve thread owner ----
        owner_id = thread.owner_id
        if not owner_id:
            await thread.send("Could not find thread author.")
            return

        owner = guild.get_member(owner_id)
        if owner is None:
            try:
                owner = await guild.fetch_member(owner_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                owner = None

        if owner is None:
            await thread.send("Looks like the author of this thread left the server.")
            return

        # ---- 4) Resolve role to give ----
        role = guild.get_role(role_id)
        if role is None:
            try:
                role = await guild.fetch_role(role_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                role = None

        if role is None:
            await thread.send("The target role does not exist (check ROLE_ID).")
            return

        # ---- 5) Assign role ----
        try:
            await owner.add_roles(
                role,
                reason=f"Applicant accepted by {author} in thread {thread.id}",
            )
        except discord.Forbidden:
            await thread.send("Cannot assign the role (permissions or role hierarchy issue).")
            return
        except discord.HTTPException:
            await thread.send("Discord API error while assigning the role. Please retry.")
            return

        # ---- 6) Confirm in thread ----
        await thread.send(f"✅ {owner.mention} accepted as **{accepted_label}**.")

        # ---- 7) Archive thread ----
        try:
            await thread.edit(archived=True, locked=False, reason="App processed")
        except discord.Forbidden:
            await thread.send("Cannot close/archive the thread (missing permissions).")
            return
        except discord.HTTPException:
            await thread.send("Discord API error while closing the thread. Please retry.")
            return

        # ---- 8) External log ----
        post_channel = await self._get_text_channel(guild, POST_CHANNEL_ID)
        if isinstance(post_channel, (discord.TextChannel, discord.Thread)):
            try:
                await post_channel.send(
                    "## New result:\n"
                    f"{owner.mention} has been accepted as **{accepted_label}**.\n"
                    f"-# Reviewed by {author.mention}."
                )
            except discord.HTTPException:
                pass  # logging failure shouldn't break the main flow

    # Group: !act <subcommand>
    @commands.guild_only()
    @commands.group(name="act", invoke_without_command=True)
    async def act(self, ctx: commands.Context):
        await ctx.reply("Usage: `!act tp` or `!act ttt`", delete_after=5)

    # Command -> !act tp
    @commands.guild_only()
    @act.command(name="tp")
    async def act_tp(self, ctx: commands.Context):
        await self._process_thread(ctx, TRIAL_ROLE_ID, "Trial Team Member")

    # Command -> !act ttt
    @commands.guild_only()
    @act.command(name="ttt")
    async def act_ttt(self, ctx: commands.Context):
        await self._process_thread(ctx, TEAM_ROLE_ID, "Team Member")


# Pycord/discord.py 2.x extension loader entrypoint
async def setup(bot: commands.Bot):
    await bot.add_cog(ThreadActions(bot))
