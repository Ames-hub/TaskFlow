from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='send', description="Send the live list to the channel.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    success = False
    try:
        await livetasks.update_for_guild(ctx.guild_id)
        success = True
    except hikari.errors.ForbiddenError:
        await ctx.edit_last_response(
            "I do not have permission to send messages in the task channel, so I rolled back changes."
        )
        # Set it back to None
        dataMan().clear_taskchannel(int(ctx.guild_id))

    if success:
        await ctx.respond(
            embed=(
                hikari.Embed(
                    title="Sent",
                    description="The live list has been sent to the live list channel."
                )
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
    else:
        await ctx.respond(
            embed=(
                hikari.Embed(
                    title="Not Sent",
                    description="We couldn't send the live list to the channel for some reason!"
                )
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
