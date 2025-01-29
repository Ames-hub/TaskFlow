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

run_update = False
auto_update = bool(os.environ.get('AUTO_UPDATE', True))
force_update = bool(os.environ.get('FORCE_UPDATE', False))

print("Auto update is set to", auto_update)
print("Force update is set to", force_update)

# Auto update logic
if auto_update is True:
    upt_file = 'data/last_update'
    os.makedirs('data', exist_ok=True)
    print("Running update check...")
    if os.path.exists(upt_file):
        with open(upt_file, 'r') as f:
            last_update = f.read()
        if len(last_update) > 1:
            last_update = datetime.datetime.fromisoformat(last_update)
            if datetime.datetime.now() - last_update < datetime.timedelta(days=2):
                print("Last update was less than 2 days ago. Skipping update.")
            else:
                print("Last update was more than 2 days ago. Running update.")
                run_update = True
        else:
            print("Last update was never recorded. Running update.")
            run_update = True
    else:
        print("Last update was never recorded. Running update.")
        run_update = True

if force_update is True:
    run_update = True

if run_update:
    update_service.run_update()
    os.makedirs('data', exist_ok=True)
    with open('data/last_update', 'w+') as f:
        f.write(str(datetime.datetime.now()))
    exit(1)  # Reboot the bot at this point.

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
