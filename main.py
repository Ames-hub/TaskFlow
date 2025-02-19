import datetime
import logging
import dotenv
import os

if not os.path.exists('.env'):
    print("Welcome to the setup process for the bot. To continue, please enter the token for the bot you want to use.")
    token = input(">>> ")
    with open('.env', 'w') as f:
        f.write(f"TOKEN={token}")

dotenv.load_dotenv('.env')

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.basicConfig(
    level=logging.ERROR,
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from library.botapp import botapp

# Loads the commands
botapp.load_extensions_from("cogs/guild_tasks/")
botapp.load_extensions_from("cogs/listeners/")
botapp.load_extensions_from("cogs/tasks/")
botapp.load_extensions_from("cogs/other")
botapp.load_extensions_from("library/")

# Creates a program-wide list to store message IDs from the bot to easily detect if we should
# Inspect a message's reactions to determine its completion status (and a couple other things)
botapp.d['watched_messages'] = {}

# A dict to track when we last edited a watched message. This is so if someone spams the reactions, it won't spam discord
botapp.d['last_edited'] = {}

botapp.d['dl_notif_cooldown'] = {}

botapp.run()
