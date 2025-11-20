import lightbulb

plugin = lightbulb.Plugin(__name__)
@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
# @lightbulb.option (options here)
# @lightbulb.add_cooldown (cooldown here)
@lightbulb.command(name='roadmap', description="What's planned? Find out here!")
@lightbulb.implements(lightbulb.SlashCommand)
async def roadmap(ctx: lightbulb.SlashContext):
    msg = (
        "The current roadmap as of 18/Nov/2025 is as follows:\n"
        "1. Continue to work on bug fixes"
        "2. Add team coordination features for task in-charges"
        "3. Find QoL Improvements that can be made"
        "\nIf you have any features you'd like to see, please use /feature_request"
    )
    await ctx.respond(msg)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
