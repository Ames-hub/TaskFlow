from library.parsing import parse_livelist_format
from datetime import datetime, timedelta
from library.storage import dataMan
import lightbulb
import logging
import hikari

CACHE_EXPIRATION_TIME = timedelta(seconds=15)
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
                completed_at = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                # If the task was completed more than 7 days ago, it will be filtered out
                if datetime.now() - completed_at > timedelta(days=7):
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
        if len(completed_tasks) + len(incomplete_tasks) == 0:
            return hikari.Embed(
                title="Live Task List",
                description="Unfortunately, there are no tasks incomplete or complete to display.",
                color=0x00ff00
            )

        try:
            guild_id = completed_tasks[0][7]
        except IndexError:
            try:
                guild_id = incomplete_tasks[0][7]
            except IndexError:
                return False

        if plugin.bot.d['livelist_styles'].get(str(guild_id)) is None:
            style = dataMan().get_livechannel_style(guild_id)
            plugin.bot.d['livelist_styles'][str(guild_id)] = [style, datetime.now().timestamp()]
        else:
            data = plugin.bot.d['livelist_styles'].get(str(guild_id))
            if data[1] + 5 < datetime.now().timestamp():
                style = dataMan().get_livechannel_style(guild_id)
                plugin.bot.d['livelist_styles'][str(guild_id)] = [style, datetime.now().timestamp()]
            else:
                style = data[0]

        embed = hikari.Embed(
            title="Live Task List",
            description=f"This is a live list of incomplete and newly completed tasks.\n{style} style",
            color=0x00ff00
        ).add_field(
            name="Details",
            value=f"The details of {len(incomplete_tasks)} incomplete task(s) is attached below.\n\n"
        )

        # Sort tasks: prioritize tasks without a category
        incomplete_tasks.sort(key=lambda task: task[8] is not None and task[8] != "")
        completed_tasks.sort(key=lambda task: task[8] is not None and task[8] != "")

        # Add completed tasks to the embed
        for task in completed_tasks:
            embed = livetasks.add_task_field(task, embed, style)

        # Categorize remaining incomplete tasks
        category_sorted_tasks = {}
        for task in incomplete_tasks:
            category = task[8] or ""  # Empty category comes first
            if category not in category_sorted_tasks:
                category_sorted_tasks[category] = []
            category_sorted_tasks[category].append(task)

        # Add sorted tasks to the embed
        for category in sorted(category_sorted_tasks.keys(), key=lambda x: x != ""):
            for task in category_sorted_tasks[category]:
                embed = livetasks.add_task_field(task, embed, style)

        return embed

    @staticmethod
    def add_task_field(task:tuple, embed, style):
        task_name = task[0]
        task_desc = task[1]
        completed = bool(task[2])
        identifier = task[3]
        added_by = task[5]
        deadline = task[6]
        guild_id = task[7]
        category = task[8]

        if style in ['classic']:
            completed_text = f"Completed: {'❌' if not completed else '✅'}"
        elif style in ['pinned', 'compact', 'minimal', 'pinned-minimal']:
            completed_text = f"{'❌' if not completed else '✅'}"
        else:
            raise ValueError("Invalid style")

        # Check cache status
        cache_result = plugin.bot.d['show_x_cache'].get(int(guild_id))

        if cache_result:
            cached_status = cache_result['status']
            cached_time = cache_result['timenow']

            # Check if the cache is still valid
            if isinstance(cached_status, bool) and (datetime.now() - cached_time) < CACHE_EXPIRATION_TIME:
                show_x = cached_status
            else:
                # Cache is outdated or invalid
                show_x = bool(dataMan().get_show_task_completion(guild_id))
                plugin.bot.d['show_x_cache'][int(guild_id)] = {
                    'status': show_x,
                    'timenow': datetime.now()
                }
        else:
            # No cache found for the guild, fetch fresh data
            show_x = bool(dataMan().get_show_task_completion(guild_id))
            plugin.bot.d['show_x_cache'][int(guild_id)] = {
                'status': show_x,
                'timenow': datetime.now()
            }

        if show_x is False and bool(completed) is False:
            completed_text = ""

        if task_desc == "...":
            task_desc = ""
        else:
            task_desc = f"{task_desc}"

        # Get task contributors
        contributors = dataMan().get_contributors(task_id=identifier)

        deadline_txt = ""
        if not completed:
            if deadline is not None:
                deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
                if deadline < datetime.now():
                    deadline_txt += f"⚠️ Deadline expired <t:{int(deadline.timestamp())}:R>!\n"
                else:
                    deadline_txt += f"Deadline: {deadline.strftime("%d/%m/%Y %I:%M %p")}\n\n"
                    deadline_txt += f"Time left: <t:{int(deadline.timestamp())}:R>\n"

        efield = embed.fields[0].value

        if category is not None and category != "":
            if style in ['classic']:
                if f"-- **__{category}__** --" not in efield:
                    efield += f"\n-- **__{category}__** --\n\n"
            elif style in ['pinned', 'pinned-minimal', 'minimal', 'compact']:
                if f"# {category}" not in efield:
                    efield += f"**__{category}__**\n"

        custom_live_text = dataMan().get_livelist_format(guild_id)

        if custom_live_text is None:
            # Quote or space
            q_or_s = '"' if len(task_desc) > 0 else ''
            no_deadline_nl = "\n" if len(deadline_txt) <= 0 else ""
            if style == 'classic':
                efield = efield + f"{task_name}\n(ID: {identifier})\n"
                efield = efield + f"{task_desc}{"\n" if len(task_desc) != 0 else ""}{completed_text}{"\n" if show_x else ""}Added by: <@{added_by}>\n{len(contributors)} helping\n{no_deadline_nl}"
            elif style == 'minimal':
                efield = efield + f"({identifier}) {task_name}{" " if show_x else ""}{completed_text}\n{no_deadline_nl}"
            elif style == 'pinned':
                efield = efield + f"- ({identifier}) {task_name}{" " if show_x else ""}{completed_text}\n{q_or_s}{task_desc}{q_or_s} {len(contributors)} people helping.\nAdded by <@{added_by}>\n{no_deadline_nl}"
            elif style == 'pinned-minimal':
                efield = efield + f"- ({identifier}) {task_name}{" " if show_x else ""}{completed_text}\n{no_deadline_nl}"
            elif style == 'compact':
                efield = efield + f"({identifier}) {task_name} {completed_text}{" " if show_x else ""}{q_or_s}{task_desc}{q_or_s} {len(contributors)} helping. <@{added_by}>\n{no_deadline_nl}"
            else:
                raise ValueError("Invalid style")

            if len(deadline_txt) > 0:
                efield = efield + f"{deadline_txt}\n"
        else:
            efield = efield + f"{parse_livelist_format(custom_live_text, task_id=identifier)}\n"
            if len(deadline_txt) > 0:
                efield = efield + f"{deadline_txt}\n"

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
