from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='channel',
    description="What channel do you want us to create the task list in?",
    type=hikari.OptionType.CHANNEL,
    required=True
)
@lightbulb.command(name='channel', description="Designate a live channel for your guild's tasks.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    task_channel: hikari.GuildChannel = ctx.options.channel

    if task_channel.type != hikari.ChannelType.GUILD_TEXT:
        await ctx.respond("The task channel must be a text channel.")
        return

    success = dataMan().set_taskchannel(int(ctx.guild_id), int(task_channel.id))
    if success:
        await ctx.respond(f"Task channel set to {task_channel.mention}")
    else:
        await ctx.respond("Failed to set task channel. Please try again later.")

    try:
        await livetasks.update(ctx.guild_id)
    except hikari.errors.ForbiddenError:
        await ctx.edit_last_response(
            "I do not have permission to send messages in the task channel, so I rolled back changes."
        )
        # Set it back to None
        dataMan().clear_taskchannel(int(ctx.guild_id))

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
