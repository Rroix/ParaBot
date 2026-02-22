import discord
from discord.ext import commands

# Only these users can run the commands
ALLOWED_USERS = {1472717671425380433}

# Announcement channel
POST_CHANNEL_ID = 1472920155968508096

# Roles
TRIAL_ROLE_ID = 1472881459864801469 # Trial Member
TEAM_ROLE_ID  = 1472725905074950226 # Team Member


class ThreadActions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _is_allowed(self, user_id: int) -> bool:
        return user_id in ALLOWED_USERS

    async def _process_thread(
        self,
        ctx: commands.Context,
        role_id: int,
        accepted_label: str,
    ):
        # Validate command interaction user
        if not self._is_allowed(ctx.author.id):
            return
        # Must be run inside a thread
        if not isinstance(ctx.channel, discord.Thread):
            await ctx.reply("You really thought you could do that, imagine...", delete_after=5)
            return

        thread: discord.Thread = ctx.channel
        guild = ctx.guild
        if not guild:
            return

        # Thread author
        owner_id = thread.owner_id
        if not owner_id:
            await thread.send("Could not find thread author")
            return

        # Resolve author of the thread to give role and mention
        owner = guild.get_member(owner_id)
        if owner is None:
            try:
                owner = await guild.fetch_member(owner_id)
            except discord.NotFound:
                owner = None

        if owner is None:
            await thread.send("Looks like the author of this thread left ParaTek")
            return

        # Role to give exists?
        role = guild.get_role(role_id)
        if not role:
            await thread.send("The role does not exist, a typo in the code prob")
            return

        # Give role
        try:
            await owner.add_roles(role, reason=f"Applicant accepted by {ctx.author} in thread {thread.id}")
        except discord.Forbidden:
            await thread.send("Cannot assign the role (perms or role hierarchy missing)")
            return
        except discord.HTTPException:
            await thread.send("Discord API error (when role), please retry")
            return

        # Message in thread
        await thread.send(f"✅ {owner.mention} accepted as **{accepted_label}**.")

        # Closes the thread. You can turn locked to True if you want to close the thread PERMANENTLY.
        try:
            await thread.edit(archived=True, locked=False, reason="App processed")
        except discord.Forbidden:
            await thread.send("Cannot close the thread (perms missing)")
            return
        except discord.HTTPException:
            await thread.send("Discord API error (when thread closing), please retry")
            return

        # External log
        post_channel = guild.get_channel(POST_CHANNEL_ID)
        if post_channel:
            await post_channel.send(
                f"## New result:\n"
                f"{owner.mention} has been accepted as **{accepted_label}**.\n"
                f"-# Reviewed by {ctx.author.mention}."
            )

    # Group: !act <subcommand>
    @commands.group(name="act", invoke_without_command=True)
    async def act(self, ctx: commands.Context):
        await ctx.reply("Usage: `!act tp` or `!act ttt`", delete_after=5)

    # Command -> !act tp
    @act.command(name="tp")
    async def act_tp(self, ctx: commands.Context):
        await self._process_thread(ctx, TRIAL_ROLE_ID, "Trial Team Member")

    # Command -> !act ttt
    @act.command(name="ttt")
    async def act_ttt(self, ctx: commands.Context):
        await self._process_thread(ctx, TEAM_ROLE_ID, "Team Member")

def setup(bot: commands.Bot):
    bot.add_cog(ThreadActions(bot))
