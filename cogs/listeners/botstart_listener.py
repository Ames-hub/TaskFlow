import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

do_print = True

@plugin.listener(hikari.events.ShardReadyEvent)
async def botstart_listener(event: hikari.events.ShardReadyEvent):
    print(f"Bot has logged in as {event.my_user.username}.")
    plugin.bot.d['is_official'] = True if event.my_user.id == 1262021444615933962 else False
    if plugin.bot.d['is_official'] and do_print:
        print("Official instance confirmed!")
        do_print = False
    else:
        print("Unofficial instance")
        do_print = False

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
