import lightbulb

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
# @lightbulb.option (options here)
# @lightbulb.add_cooldown (cooldown here)
@lightbulb.command(name='template', description='A template command')
@lightbulb.implements(lightbulb.SlashCommand)
async def template(ctx: lightbulb.SlashContext):
    await ctx.respond('This is a template command')

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
