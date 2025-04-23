from datetime import datetime, timedelta
from library.storage import dataMan
from library.botapp import botapp
from lightbulb.ext import tasks
from library.perms import perms
import lightbulb
import logging
import hikari
import dotenv
import os

dotenv.load_dotenv('.env')
plugin = lightbulb.Plugin(__name__)
DEBUG = os.environ.get("DEBUG").lower() == "true"

@tasks.task(s=15 if DEBUG is False else 3, wait_before_execution=False, auto_start=True)
async def task() -> None:
    task_list = dataMan().get_todo_items(filter_for='incompleted')
    # Group the tasks by guild
    group_tasks = {}
    for task in task_list:
        guild_id = task[7]
        if group_tasks.get(guild_id) is None:
            group_tasks[guild_id] = []
        group_tasks[guild_id].append(task)

    for guild_id in group_tasks:
        embed = (
            hikari.Embed(
                title="Deadline Tasks",
                description="This is a complete list of all tasks that are overdue for their deadline, or soon will be for the server."
            )
        )

        # These will be added to an embed field at the end
        nearing_txt = ""
        overdue_txt = ""

        for task in group_tasks[guild_id]:
            name = task[0]
            completed = bool(task[2])
            uuid = task[3]
            if completed:
                continue

            if botapp.d['dl_notif_cooldown'].get(uuid) is not None:
                # Make sure to not continue unless it has been 2 hours since the last notification
                if datetime.now() - botapp.d['dl_notif_cooldown'][uuid] < timedelta(hours=2):
                    continue

            deadline: str = task[6]

            if deadline is None:
                continue

            HMS = None
            if " " in deadline:
                HMS = deadline.split(" ")[1]

            if HMS:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
            else:
                deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")

            now = datetime.now()

            if now > deadline_dt:
                overdue_txt += f"{name} ({uuid})\n"
                overdue_txt += f"Deadline overdue <t:{int(deadline_dt.timestamp())}:R>!\n"
                overdue_txt += f"Due at <t:{int(deadline_dt.timestamp())}:F>\n\n"
            elif now < deadline_dt and deadline_dt - now < timedelta(hours=12):
                nearing_txt += f"{name} ({uuid})\n"
                nearing_txt += f"The Deadline is approaching! <t:{int(deadline_dt.timestamp())}:R>!\n"
                nearing_txt += f"Due at: <t:{int(deadline_dt.timestamp())}:F>\n\n"
            else:
                continue

            botapp.d['dl_notif_cooldown'][uuid] = datetime.now()

        livetask_channel_id = dataMan().get_taskchannel(int(guild_id))

        if livetask_channel_id is None:
            continue

        if overdue_txt != "":
            embed.add_field(
                name="Overdue Tasks",
                value=overdue_txt,
                inline=True
            )
        if nearing_txt != "":
            embed.add_field(
                name="Tasks Nearing Deadline",
                value=nearing_txt,
                inline=True
            )

        if nearing_txt == "" and overdue_txt == "":
            continue  # No tasks to send!

        try:
            await botapp.rest.create_message(
                hikari.Snowflake(livetask_channel_id),
                embed=embed
            )
        except hikari.errors.ForbiddenError:
            logging.info(f"I can't send messages in {guild_id}!")
            continue
        except hikari.errors.NotFoundError:
            logging.info(f"The task channel for {guild_id} doesn't exist! Removing it from the database.")
            dataMan().clear_taskchannel(int(guild_id))

            # Gets the Guild Owner user ID. This should always be an ID unless discord its self is having issues.
            guild_owner = await perms.get_guild_owner_id(guild_id)

            guild_name = plugin.bot.cache.get_guild(int(guild_id)).name
            if guild_name is None:
                guild_id = await plugin.bot.rest.fetch_guild(int(guild_id))
                guild_name = str(guild_id.name)

            dmc = await plugin.bot.rest.create_dm_channel(guild_owner)

            embed = (
                hikari.Embed(
                    title="Task Channel 404",
                    description=f"The live list channel for {guild_name} could not be found!\n"
                                "If you want to set the task channel to something new, use `/live channel`\n"
                                "If you think this is a bug, please report it to the developer using /bug_report\n"
                                "Thank you for using TaskFlow!\n"
                )
            )

            await dmc.send(embed)

            continue

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))