from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)
dm = dataMan()

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='resetdesc', description="Reset the description for your server's live list", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):

    success = dm.set_livelist_description(None, ctx.guild_id)

    if success:
        await ctx.respond(
            hikari.Embed(
                title="Description cleared",
                description="The description has been successfully cleared."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Something went wrong and we couldn't do it! :( We're tracking the error now."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    await livetasks.update(ctx.guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
