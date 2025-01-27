from lightbulb.ext import tasks
import lightbulb
import hikari
import os

intents = [
    hikari.Intents.MESSAGE_CONTENT,
    hikari.Intents.GUILD_MESSAGE_REACTIONS,
    hikari.Intents.DM_MESSAGE_REACTIONS
]
# Calculates perm bits for the bot's intents.
intent_val = 0
for intent in intents:
    intent_val += intent

botapp = lightbulb.BotApp(
    token=os.environ.get("TOKEN", None),
    intents=intent_val
)
tasks.load(botapp)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))
