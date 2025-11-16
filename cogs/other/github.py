import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
# @lightbulb.option (options here)
# @lightbulb.add_cooldown (cooldown here)
@lightbulb.command(name='github', description='Find the bots github repository and who made the bot!')
@lightbulb.implements(lightbulb.SlashCommand)
async def github_linking(ctx: lightbulb.SlashContext):
    msg = (
        "This bot is free and open source! Meaning you can host it yourself, or even contribute to the code!\n\n"
        "https://github.com/Ames-hub/TaskFlow\n"
        "https://github.com/Ames-hub"
    )
    embed = (
        hikari.Embed(
            title="GitHub Repository",
            description=msg,
            color=hikari.Color(0x7289DA)
        )
    )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
