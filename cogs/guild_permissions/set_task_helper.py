from cogs.guild_permissions.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='role',
    description="Which role is the one that helps out in tasks",
    required=True,
    type=hikari.OptionType.ROLE,
)
@lightbulb.command(name='helprole', description='Set the task helper role!', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext, role:hikari.Role):
    dm = dataMan()
    success = dm.set_taskmaster_role(ctx.guild_id, role.id)

    if success:
        await ctx.respond(
            embed=hikari.Embed(
                title="Success!",
                description="The helper role was set."
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
