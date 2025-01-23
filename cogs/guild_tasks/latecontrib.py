from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='allowed',
    description='Can users contribute to completed tasks late?',
    required=True,
    type=hikari.OptionType.BOOLEAN,
)
@lightbulb.command(name='latecontrib', description='Set if users can contribute to completed tasks late.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def latecontrib_cmd(ctx: lightbulb.SlashContext):
    allowed = ctx.options['allowed']
    dataMan().set_allow_late_contrib(int(ctx.guild_id), bool(allowed))

    await ctx.respond(f"Users can now contribute to completed tasks late. (after completion)" if allowed else f"Users can no longer contribute to completed tasks late.")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
