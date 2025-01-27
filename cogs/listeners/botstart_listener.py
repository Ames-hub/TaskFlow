import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(hikari.events.ShardReadyEvent)
async def botstart_listener(event: hikari.events.ShardReadyEvent):
    print(f"Bot has logged in as {event.my_user.username}.")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
