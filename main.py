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

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

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
botapp.load_extensions_from("cogs/guild_permissions/")
# botapp.load_extensions_from("cogs/task_incharge/")
botapp.load_extensions_from("cogs/task_templates/")
botapp.load_extensions_from("cogs/guild_tasks/")
botapp.load_extensions_from("cogs/livechannel/")
botapp.load_extensions_from("cogs/listeners/")
botapp.load_extensions_from("cogs/tasks/")
botapp.load_extensions_from("cogs/other")
botapp.load_extensions_from("library/")

# MAIN VARIABLES
botapp.d['max_name_length'] = 150
botapp.d['max_desc_length'] = 2000

# Creates a program-wide list to store message IDs from the bot to easily detect if we should
# Inspect a message's reactions to determine its completion status (and a couple other things)
botapp.d['watched_messages'] = {}

# A dict to track when we last edited a watched message. This is so if someone spams the reactions, it won't spam discord
botapp.d['last_edited'] = {}

botapp.d['reaction_cooldown'] = 0  # seconds
botapp.d['dl_notif_cooldown'] = {}

# The same colour as the dark-mode embed body. This gives a clean look to the embed.
botapp.d['colourless'] = 0x2b2d31

botapp.d['livelist_styles'] = {}

botapp.d['DEBUG'] = DEBUG

botapp.d['show_x_cache'] = {}

botapp.d['guild_owner_ids_cache'] = {}

botapp.d['servercount_memory'] = {
    'count': None,
    'last_updated': None,
}

botapp.run(shard_count=5 if DEBUG is False else 1)
