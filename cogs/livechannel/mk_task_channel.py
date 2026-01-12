from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='channelname',
    description="What do you want us to call the channel?",
    type=hikari.OptionType.STRING,
    required=True
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='makechannel', description="Create a live channel for your guild's tasks.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):

    server_perm = dataMan().get_guild_configperm(ctx.guild_id)
    allowed = await perms.is_privileged(
        guild_id=ctx.guild_id,
        user_id=ctx.author.id,
        permission=server_perm
    )
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, missing_perm=server_perm)
        return

    # Create the channel
    try:
        guild = ctx.get_guild()
        if not guild:
            guild = await plugin.bot.rest.fetch_guild(ctx.guild_id)
        
        task_channel = await guild.create_text_channel(
            name=ctx.options.channelname,
            reason="Creating live task channel as requested by command."
        )
    except (hikari.ForbiddenError, hikari.UnauthorizedError):
        await ctx.respond("I do not have permission to create channels in this server.")
        return
    except hikari.BadRequestError:
        await ctx.respond("The channel name provided is invalid.")
        return

    success = dataMan().set_taskchannel(int(ctx.guild_id), int(task_channel.id))
    if success:
        await ctx.respond(f"Task channel set to <#{task_channel.id}>")
    else:
        await ctx.respond("Failed to set task channel. Please try again later.", flags=hikari.MessageFlag.EPHEMERAL)

    try:
        await livetasks.update_for_guild(ctx.guild_id)
    except hikari.errors.ForbiddenError:
        # Set it back to None
        dataMan().clear_taskchannel(int(ctx.guild_id))

        # Alert user
        await ctx.author.send(
            "I do not have permission to send messages in the task channel, so I rolled back changes."
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
