import hikari
import lightbulb

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='news', description="Find out what's new in the bot!")
@lightbulb.implements(lightbulb.SlashCommand)
async def news_cmd(ctx: lightbulb.SlashContext):
    # TODO: Make a system that fetches from a server the 'latest message', for now, we do this.
    msg = ("As of 1/04/2025, We fixed a previously unseen error logic which made the X or Check never appear if xtoggle was False.\n"
           "Apologies for any inconveniences this may have caused! If you see anything that doesn't seem right, it likely isn't meant to be like that.\n"
           "Feel free to DM @friendlyfox.exe at any point for a correction in the bot.")

    await ctx.respond(
        hikari.Embed(
            title="Bulletin 1/04/2025",
            description=msg
        )
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
