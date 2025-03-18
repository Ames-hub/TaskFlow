from cogs.livechannel.views.taskmenu import views
from cogs.guild_tasks.group import group
from library.botapp import miru_client
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='list', description="The task select GUI.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    view = views(ctx.guild_id)
    view_menu = view.init_view()
    await ctx.respond(
        embed=view.gen_init_embed(),
        components=view_menu.build(),
        flags=hikari.MessageFlag.EPHEMERAL
    )

    miru_client.start_view(view_menu)
    await view_menu.wait()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
