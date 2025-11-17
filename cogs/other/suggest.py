from cogs.other.views.suggestions.suggestion_view import main_view
from library.botapp import miru_client
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='feature_request', description='Make a feature request!')
@lightbulb.implements(lightbulb.SlashCommand)
async def bug_report(ctx: lightbulb.SlashContext):
    view = main_view(int(ctx.author.id))
    embed = view.gen_embed()
    viewmenu = view.init_view()
    await ctx.respond(flags=hikari.MessageFlag.EPHEMERAL, embed=embed, components=viewmenu.build())
    miru_client.start_view(viewmenu)
    await viewmenu.wait()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
