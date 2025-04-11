from cogs.guild_permissions.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='clearhelprole', description='Clear the task helper role.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext):
    dm = dataMan()
    success = dm.set_taskmaster_role(ctx.guild_id, 0)

    if success:
        await ctx.respond(
            embed=hikari.Embed(
                title="Success!",
                description="The helper role was cleared."
            )
        )
    else:
        await ctx.respond(
            embed=hikari.Embed(
                title="Uh oh!",
                description="Something didn't go right! We're tracking the error now."
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
