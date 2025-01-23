import lightbulb
import hikari
import dotenv
import os

if not os.path.exists('secrets.env'):
    print("Welcome to the setup process for the bot. To continue, please enter the token for the bot you want to use.")
    token = input(">>> ")
    with open('secrets.env', 'w') as f:
        f.write(f"TOKEN={token}")

dotenv.load_dotenv('secrets.env')

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

# Loads the commands
botapp.load_extensions_from("cogs/guild_tasks/")
botapp.load_extensions_from("cogs/listeners/")
botapp.load_extensions_from("cogs/other")
botapp.load_extensions_from("library/")

# Creates a program-wide list to store message IDs from the bot to easily detect if we should
# Inspect a message's reactions to determine its completion status (and a couple other things)
botapp.d['watched_messages'] = {}

# A dict to track when we last edited a watched message. This is so if someone spams the reactions, it won't spam discord
botapp.d['last_edited'] = {}

botapp.run()
