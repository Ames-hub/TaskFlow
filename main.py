from updater import update_service
import datetime
import logging
import dotenv
import os

if not os.path.exists('secrets.env'):
    print("Welcome to the setup process for the bot. To continue, please enter the token for the bot you want to use.")
    token = input(">>> ")
    with open('secrets.env', 'w') as f:
        f.write(f"TOKEN={token}")

dotenv.load_dotenv('secrets.env')

if bool(os.environ.get('AUTO_UPDATE', True)) is True:
    upt_file = 'data/last_update'
    os.makedirs('data', exist_ok=True)
    if os.path.exists(upt_file):
        with open(upt_file, 'r') as f:
            last_update = f.read()
        if last_update:
            last_update = datetime.datetime.fromisoformat(last_update)
            if datetime.datetime.now() - last_update < datetime.timedelta(days=2):
                print("Last update was less than 2 days ago. Skipping update.")
                exit(0)

    update_service.run_update()
    os.makedirs('data', exist_ok=True)
    with open('data/last_update', 'w+') as f:
        f.write(str(datetime.datetime.now()))
    exit(0)  # Reboot the bot at this point.

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

botapp.run()
