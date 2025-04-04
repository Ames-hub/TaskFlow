from library.storage import dataMan
from lightbulb.ext import tasks
from datetime import datetime, timedelta
from library.botapp import botapp
import lightbulb
import logging
import hikari

plugin = lightbulb.Plugin(__name__)

@tasks.task(s=4, wait_before_execution=True, auto_start=True)
async def task() -> None:
    # TODO: Fix the fact that the below call recieves 0 tasks
    task_list = dataMan().get_todo_items(filter_for='incompleted')
    for task in task_list:
        name = task[0]
        description = task[1]
        completed = bool(task[2])
        uuid = task[3]
        adder_id = task[5]
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

        # Assuming the deadline format is 'DD/MM/YYYY' or 'DD/MM/YYYY HH:MM:SS'
        if HMS:
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
        else:
            deadline_dt = datetime.strptime(deadline, "%Y-%m-%d")

        now = datetime.now()

        if now > deadline_dt:
            embed = (
                hikari.Embed(
                    title=f"{name} ({uuid})",
                    description=description if description != "..." else "No description provided.",
                    color=hikari.Color(0xFF0000)
                )
                .add_field(name="Deadline", value=f"Deadline overdue <t:{int(deadline_dt.timestamp())}:R>!"
                                                  f"\n<t:{int(deadline_dt.timestamp())}:F>"
                                                  f"\n<@{adder_id}>")
            )
        elif datetime.fromtimestamp(now.timestamp() - 43200) > deadline_dt:
            embed = (
                hikari.Embed(
                    title=f"{name} ({uuid})",
                    description=description,
                    color=hikari.Color(0xFFFF00)
                )
                .add_field(name="Deadline", value=f"Deadline is approaching!"
                                                  f"\n<t:{int(deadline_dt.timestamp())}:R>"
                                                  f"\n<t:{int(deadline_dt.timestamp())}:F>")
            )
        else:
            continue

        guild_id = dataMan().crossref_task(task_id=uuid)

        if guild_id is None:
            continue  # This task is not associated with any guild, so we can't send a message about it.

        livetask_channel_id = dataMan().get_taskchannel(int(guild_id))

        if livetask_channel_id is None:
            continue

        try:
            await botapp.rest.create_message(
                hikari.Snowflake(livetask_channel_id),
                embed=embed
            )
            botapp.d['dl_notif_cooldown'][uuid] = datetime.now()
        except hikari.errors.ForbiddenError:
            logging.info(f"I can't send messages in {guild_id}!")
            continue

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))