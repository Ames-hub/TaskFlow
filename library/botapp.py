from lightbulb.ext import tasks
import lightbulb
import dotenv
import hikari
import miru
import os

dotenv.load_dotenv('.env')

intents = [
    hikari.Intents.GUILDS,
    hikari.Intents.GUILD_MESSAGES,  # TODO: Find out what the hell is listening for MessageDeleteEvent
]
# Calculates perm bits for the bot's intents.
intent_val = 0
for intent in intents:
    intent_val += intent

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

botapp = lightbulb.BotApp(
    token=os.environ.get("TOKEN" if DEBUG is False else "DEBUG_TOKEN", None),
    intents=intent_val
)
tasks.load(botapp)
miru_client = miru.Client(botapp)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))
