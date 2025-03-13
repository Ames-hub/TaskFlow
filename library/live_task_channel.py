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

        embed = livetasks.gen_livetasklist_embed(completed_tasks, incomplete_tasks)
        if embed is False:
            try:
                await plugin.bot.rest.create_message(
                    embed=(
                        hikari.Embed(
                            title="Uh oh!",
                            description="Failed to generate embed for live task list!"
                        ),
                    ),
                    channel=task_channel
                )
                return False
            except hikari.errors.NotFoundError:
                logging.info(f"Task channel for guild {guild_id} not found. Disabling live task list.")
                dataMan().clear_taskchannel(guild_id)
                return False

        try:
            await plugin.bot.rest.create_message(embed=embed, channel=task_channel)
        except hikari.errors.NotFoundError:
            logging.info(f"Task channel for guild {guild_id} not found. Disabling live task list.")
            dataMan().clear_taskchannel(guild_id)
            return False

        return True

    @staticmethod
    def gen_livetasklist_embed(completed_tasks, incomplete_tasks):
        # Gets the guild's livelist style setting with a 5-second cache
        # Grabs the first task's guild ID. Since the guild id will be the same for all these tasks
        try:
            guild_id = completed_tasks[0][7]
        except IndexError:
            try:
                guild_id = incomplete_tasks[0][7]
            except IndexError:
                return False
        if plugin.bot.d['livelist_styles'].get(str(guild_id)) is None:
            style = dataMan().get_livechannel_style(guild_id)
            plugin.bot.d['livelist_styles'][str(guild_id)] = [style, datetime.datetime.now().timestamp()]
        else:
            data = plugin.bot.d['livelist_styles'].get(str(guild_id))
            if data[1] + 5 < datetime.datetime.now().timestamp():
                style = dataMan().get_livechannel_style(guild_id)
                plugin.bot.d['livelist_styles'][str(guild_id)] = [style, datetime.datetime.now().timestamp()]
            else:
                style = data[0]

        embed = (
            hikari.Embed(
                title="Live Task List",
                description=f"This is a live list of incomplete and newly completed tasks.\n{style} style",
                color=0x00ff00
            )
            .add_field(
                name="Details",
                value=f"The details of {len(incomplete_tasks)} incomplete task(s) is attached below.\n\n"
            )
        )

        # Adds all the completed tasks to the top of the embed (seemingly less important, as we see bottom-to-top)
        for task in completed_tasks:
            embed = livetasks.add_task_field(task, embed, style)

        # Counts the amount of tasks in each category
        task_cat_count = {}
        for task in incomplete_tasks:
            category = str(task[8])
            if category not in task_cat_count.keys():
                task_cat_count[category] = 1
            else:
                task_cat_count[category] += 1

        category_sorted_tasks = {}
        # Organizes tasks by category
        for task in incomplete_tasks:
            category = str(task[8])
            # Makes sure the category has at least one task
            if task_cat_count[category] == 0:
                continue

            if category not in category_sorted_tasks.keys():
                category_sorted_tasks[category] = []

            # noinspection PyUnresolvedReferences
            category_sorted_tasks[category].append(task)

        # Adds all the completed tasks to the bottom of the embed
        for category in category_sorted_tasks:
            for task in category_sorted_tasks[category]:
                embed = livetasks.add_task_field(task, embed, style)

        return embed

    @staticmethod
    def add_task_field(task:tuple, embed, style):
        task_name = task[0]
        task_desc = task[1]
        completed = task[2]
        identifier = task[3]
        added_by = task[5]
        deadline = task[6]
        category = task[8]

        if style in ['classic']:
            completed_text = f"Completed: {'❌' if not completed else '✅'}"
        elif style in ['pinned', 'compact', 'minimal', 'pinned-minimal']:
            completed_text = f"{'❌' if not completed else '✅'}"
        else:
            raise ValueError("Invalid style")

        if task_desc == "...":
            task_desc = ""
        else:
            task_desc = f"{task_desc}"

        # Get task contributors
        contributors = dataMan().get_contributors(task_id=identifier)

        deadline_txt = ""
        if deadline is not None:
            deadline = datetime.datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
            if deadline < datetime.datetime.now():
                deadline_txt += f"⚠️ Deadline expired <t:{int(deadline.timestamp())}:R> ago!\n"
            else:
                deadline_txt += f"Deadline: {deadline.strftime("%d/%m/%Y %I:%M %p")}\n"
                deadline_txt += f"Time left: <t:{int(deadline.timestamp())}:R>\n"

        efield = embed.fields[0].value

        if category is not None:
            if style in ['classic']:
                if f"-- **__{category}__** --" not in efield:
                    efield += f"\n-- **__{category}__** --\n\n"
            elif style in ['pinned', 'pinned-minimal', 'minimal', 'compact']:
                if f"# {category}" not in efield:
                    efield += f"**__{category}__**\n"

        # Quote or space
        q_or_s = '"' if len(task_desc) > 0 else ''
        if style == 'classic':
            efield = efield + f"{task_name}\n(ID: {identifier})\n"
            efield = efield + f"{task_desc}{completed_text}\nAdded by: <@{added_by}>\n{len(contributors)} helping\n\n"
        elif style == 'minimal':
            efield = efield + f"({identifier}) {task_name} {completed_text}\n"
        elif style == 'pinned':
            efield = efield + f"- ({identifier}) {task_name} {completed_text}\n{q_or_s}{task_desc}{q_or_s} {len(contributors)} people helping.\nAdded by <@{added_by}>\n"
        elif style == 'pinned-minimal':
            efield = efield + f"- ({identifier}) {task_name} {completed_text}\n"
        elif style == 'compact':
            efield = efield + f"({identifier}) {task_name} {completed_text} {q_or_s}{task_desc}{q_or_s} {len(contributors)} helping. <@{added_by}>\n"
        else:
            raise ValueError("Invalid style")

        efield = efield + deadline_txt

        embed.edit_field(
            0,
            "Details",
            efield,
            inline=False
        )

        return embed

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
