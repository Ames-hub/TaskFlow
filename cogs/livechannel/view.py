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
@lightbulb.command(name='view', description="View the live list privately!")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    success = False
    try:
        await livetasks.update_to_target(ctx.guild_id, target_user_id=ctx.author.id)
        success = True
    except hikari.ForbiddenError:
        await ctx.respond(
            hikari.Embed(
                title="Bad permissions!",
                description="I do not have permission to send messages in your DMs!",
                color=0xFF0000
            )
        )
        return

    if success:
        await ctx.respond(
            embed=(
                hikari.Embed(
                    title="Sent",
                    description="The live list has been sent to your DMs."
                )
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
    else:
        await ctx.respond(
            embed=(
                hikari.Embed(
                    title="Not Sent",
                    description="We couldn't send the live list to your DMs for some reason!"
                )
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
