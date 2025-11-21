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
    name='setchannel',
    description="What channel do you want us to create the task list in?",
    type=hikari.OptionType.CHANNEL,
    required=True
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='setchannel', description="Designate a live channel for your guild's tasks.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    task_channel: hikari.GuildChannel = ctx.options.setchannel

    allowed = await perms.is_privileged(
        guild_id=ctx.guild_id,
        user_id=ctx.author.id,
        permission=dataMan().get_guild_configperm(ctx.guild_id)
    )
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, missing_perm="Manage Server")
        return

    if task_channel.type != hikari.ChannelType.GUILD_TEXT:
        await ctx.respond("The task channel must be a text channel.")
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
