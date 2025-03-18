from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='send', description="Send the live list to the channel.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    await ctx.respond(
        embed=(
            hikari.Embed(
                title="Sent",
                description="The live list has been sent to the live list channel."
            )
        ),
        flags=hikari.MessageFlag.EPHEMERAL
    )
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
