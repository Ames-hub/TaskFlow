from library.live_task_channel import livetasks
from datetime import datetime, timedelta
from library.storage import dataMan
from library.botapp import botapp
from lightbulb.ext import tasks
import lightbulb
import logging
import dotenv
import hikari
import os

dotenv.load_dotenv('.env')
plugin = lightbulb.Plugin(__name__)
DEBUG = os.environ.get("DEBUG", 'false').lower() == "true"

@tasks.task(
    h=6 if DEBUG is False else 0,
    s=15 if DEBUG is True else 0,  # Shorten delay in debug mode.
    wait_before_execution=False,
    auto_start=True
)
async def task() -> None:
    recur_list = dataMan().get_recur_list()

    # Goes through each item in the list and counts how many guilds are queued
    guild_recur_counter = {}
    for recur_item_id in recur_list:
        guild_id = recur_list[recur_item_id]['guild_id']
        guild_recur_counter[guild_id] = guild_recur_counter.get(guild_id, 0) + 1

    guild_recur_done_counter = {}
    for recur_item_id in recur_list:
        template_id = recur_list[recur_item_id]['template_id']
        guild_id = recur_list[recur_item_id]['guild_id']
        last_recur = datetime.strptime(recur_list[recur_item_id]['last_recur'], "%Y-%m-%d %H:%M:%S")
        recur_interval = recur_list[recur_item_id]['interval']
        blame_id = recur_list[recur_item_id]['blame_id']

        guild_recur_done_counter[guild_id] = guild_recur_done_counter.get(guild_id, 0) + 1

        # Checks if it's time to recur
        if last_recur > datetime.now() - timedelta(days=recur_interval):
            if DEBUG:
                logging.debug(f"RECURRANCE MANAGER: ITEM {recur_item_id}, SKIP. Last recur: {recur_list[recur_item_id]['last_recur']}.")
            continue

        try:
            task_id = dataMan().create_task_from_template(
                template_id=template_id,
                task_creator_id=blame_id,
                guild_id=guild_id,
                return_ticket=True
            )
            if DEBUG:
                logging.debug(f"RECURRANCE MANAGER: ITEM {recur_item_id}, SUCCESSFUL TASK CREATION.")

            update_success = dataMan().update_last_recur(recur_item_id, task_id)
            if update_success:
                if DEBUG:
                    logging.debug(f"RECURRANCE MANAGER: ITEM {recur_item_id}, SUCCESSFUL LAST_RECUR UPDATE.")
            else:
                if DEBUG:
                    logging.debug(f"RECURRANCE MANAGER: ITEM {recur_item_id}, FAILED LAST_RECUR UPDATE.")
                continue

            # Only send the update message if all recurring tasks for that guild are processed.
            if guild_recur_done_counter.get(guild_id, 0) == guild_recur_counter.get(guild_id, 0):
                await livetasks.update_for_guild(guild_id)
        except Exception as err:
            if DEBUG:
                logging.debug(f"RECURRANCE MANAGER: ITEM {recur_item_id}, FAILED TASK CREATION. SEE LOGS.")
            logging.error(err)
            # Alert the server of the fail
            task_channel_id = dataMan().get_taskchannel(guild_id)
            try:
                await botapp.rest.create_message(
                    task_channel_id,
                    embed=hikari.Embed(
                        title="Error",
                        description=f"Error creating recurring task for template {template_id}."
                    )
                )
            except (hikari.ForbiddenError, hikari.UnauthorizedError):
                logging.warning(f"Unable to send error message to task channel with ID {task_channel_id} for guild {guild_id}.")

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))