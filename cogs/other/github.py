import lightbulb

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
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
    await ctx.respond(msg)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
