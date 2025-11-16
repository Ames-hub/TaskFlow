import datetime
import logging
import asyncio
import uvicorn
import dotenv
import os

if not os.path.exists('.env'):
    print("Welcome to the setup process for the bot. To continue, please enter the token for the bot you want to use.")
    token = input(">>> ")

    print("Thank you. What is your discord UUID?")
    uuid = input(">>> ")

    text = f"""
TOKEN={token}\n
PRIMARY_MAINTAINER_ID={uuid}
    """

    # Write a .env file for next time.
    with open('.env', 'a') as f:
        f.write(text)

    print("Process completed. Starting bot.")

dotenv.load_dotenv('.env')

DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.basicConfig(
    level=logging.WARNING,
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.basicConfig(
    level=logging.ERROR,
    filename=f'logs/{datetime.datetime.now().strftime("%Y-%m-%d")}.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.basicConfig(
    level=logging.DEBUG,
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
botapp.load_extensions_from("cogs/task_recur/")
botapp.load_extensions_from("cogs/listeners/")
botapp.load_extensions_from("cogs/tasks/")
botapp.load_extensions_from("cogs/other")
botapp.load_extensions_from("library/")

# MAIN VARIABLES
botapp.d['max_name_length'] = 150
botapp.d['max_desc_length'] = 1850  # 150 + 1850 = 2000 characters (Discord limit)

botapp.d['reaction_cooldown'] = 0  # seconds
botapp.d['dl_notif_cooldown'] = {}

# The same colour as the dark-mode embed body. This gives a clean look to the embed.
botapp.d['colourless'] = 0x2b2d31

# A Cache for the livelist styles of servers.
botapp.d['livelist_styles'] = {}

botapp.d['DEBUG'] = DEBUG

# A Cache for if we should show the incompletion marker on incomplete to do items.
botapp.d['show_x_cache'] = {}

# This is for setting who can do certain things
botapp.d['PRIMARY_MAINTAINER_ID'] = int(os.getenv('PRIMARY_MAINTAINER_ID', 913574723475083274))

# Used to track bot uptime and ensure certain tasks don't run too early.
botapp.d['INIT_TIME'] = int(datetime.datetime.now().timestamp())

# Used by the bot to cache stuff.
botapp.d['guild_owner_ids_cache'] = {}

botapp.d['servercount_memory'] = {
    'count': None,
    'last_updated': None,
}

botapp.d['priority_map'] = {
    'alnum': {
        'Urgent': 5,
        'High': 4,
        'Medium': 3,
        'Normal': 2,
        'Low': 1
    },
    'numeric': {
        5: 'Urgent',
        4: 'High',
        3: 'Medium',
        2: 'Normal',
        1: 'Low'
    }
}

botapp.d['member_counting'] = {}

async def main():
    config = uvicorn.Config(
        "webpanel.webpanel:fastapp",
        host="0.0.0.0" if not DEBUG else "127.0.0.1",
        port=8015,
        loop="asyncio",
        lifespan="on",
        reload=False
    )
    server = uvicorn.Server(config)

    await asyncio.gather(
        server.serve(),
        botapp.start(shard_count=25 if not DEBUG else 1)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Ending process.")
