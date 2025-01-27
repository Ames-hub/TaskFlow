from library.storage import dataMan
import lightbulb
import datetime
import logging
import hikari

plugin = lightbulb.Plugin(__name__)
class livetasks:
    @staticmethod
    async def update(guild_id):
        incomplete_tasks = dataMan().get_todo_items(guild_id=int(guild_id), filter_for='incompleted')
        unfiltered_completed_tasks = dataMan().get_todo_items(guild_id=int(guild_id), filter_for='completed')
        task_channel = dataMan().get_taskchannel(int(guild_id))

        if task_channel is None:
            return False

        # Filters out completed tasks that have been completed for more than 7 days
        # This is to prevent the list from getting too long.
        completed_tasks = []
        for task in unfiltered_completed_tasks:
            completed = task[2]
            if completed:
                completed_at = task[4]  # eg, 2024-07-15 18:52:16. Type str
                # Converts to datetime obj
                completed_at = datetime.datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                # If the task was completed more than 7 days ago, it will be filtered out
                if datetime.datetime.now() - completed_at > datetime.timedelta(days=7):
                    continue
                else:
                    completed_tasks.append(task)

        embed = (
            hikari.Embed(
                title="Live Task List",
                description="This is a live list of incomplete and newly completed tasks.",
                color=0x00ff00
            )
        )

        # Adds all the completed tasks to the top of the embed (seemingly less important, as we see bottom-to-top)
        for task in completed_tasks:
            embed = livetasks.add_task_field(task, embed)
        # Adds all the completed tasks to the bottom of the embed
        for task in incomplete_tasks:
            embed = livetasks.add_task_field(task, embed)

        footer_text = ("This list is updated on events.\n"
                       "To interact with a task, use /grouptasks view (task id)")
        embed.set_footer(text=footer_text)

        try:
            await plugin.bot.rest.create_message(embed=embed, channel=task_channel)
        except hikari.errors.NotFoundError:
            logging.info(f"Task channel for guild {guild_id} not found. Disabling live task list.")
            dataMan().clear_taskchannel(guild_id)
            return False

        return True

    @staticmethod
    def add_task_field(task:tuple, embed):
        task_name = task[0]
        task_desc = task[1]
        completed = task[2]
        identifier = task[3]
        added_by = task[5]

        completed_text = f"Completed: {'❌' if not completed else '✅'}"

        if task_desc == "...":
            task_desc = "\n"
        else:
            task_desc = f"{task_desc}\n\b"

        # Get task contributors
        contributors = dataMan().get_contributors(task_id=identifier)

        embed.add_field(
            name=f"{task_name}\n(ID: {identifier})",
            value=f"{task_desc}{completed_text}\nAdded by: <@{added_by}>\n{len(contributors)} Contributors",
            inline=False
        )
        return embed

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
