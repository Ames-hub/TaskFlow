from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.storage import dataMan
from library import tferror
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='update', description="Send the live list to the channel.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    success = False
    try:
        await livetasks.update_for_guild(ctx.guild_id, bypass_cooldown=True)
        success = True
    except hikari.errors.ForbiddenError:
        await ctx.respond(
            hikari.Embed(
                title="Bad permissions!",
                description="I do not have permission to send messages in the task channel!",
                color=0xFF0000
            )
        )
        return
    except tferror.livelist.no_channel:
        await ctx.respond(
            hikari.Embed(
                title="No channel set!",
                description="To do this, we need a set live list channel, but that isn't set for this server! Please set it with `/livelist setchannel`",
                color=0xFF0000
            )
        )

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
