import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='kofi', description='See our Kofi!')
@lightbulb.implements(lightbulb.SlashCommand)
async def legal(ctx: lightbulb.SlashContext):
    embed = (
        hikari.Embed(
            title="Support Us 💚",
            description=(
                "This bot is created and maintained completely free of charge.\n"
                "If you'd like to support us and help cover the cost of time, so we can spend much more time building "
                "this project, I'd truly appreciate it!\n\n[Click Here to view our Kofi!](https://ko-fi.com/ameshub)"
            )
        )
    )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
