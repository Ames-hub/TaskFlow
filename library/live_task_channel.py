from library.parsing import parse_livelist_format
from datetime import datetime, timedelta
from library.storage import dataMan
import lightbulb
import logging
import random
import hikari

CACHE_EXPIRATION_TIME = timedelta(seconds=15)
plugin = lightbulb.Plugin(__name__)

class livetasks:
    @staticmethod
    def filter_out_old_completed_tasks(task_list):
        completed_tasks = []
        for task in task_list:
            completed = task[2]
            if completed:
                completed_at = task[4]  # eg, 2024-07-15 18:52:16. Type str
                # Converts to datetime obj
                completed_at = datetime.strptime(completed_at, "%Y-%m-%d %H:%M:%S")
                # If the task was completed more than some days ago, it will be filtered out
                if datetime.now() - completed_at > timedelta(days=3):
                    continue
                else:
                    completed_tasks.append(task)
        return completed_tasks

    @staticmethod
    async def update_to_target(guild_id, target_user_id=None, target_channel_id:int=None):
        """
        A Function to update the live task list to a target channel or user.
        """

        if target_user_id is None:
            target_channel_id = int(target_channel_id)
        else:
            target_user_id = int(target_user_id)

        guild_id = int(guild_id)

        incomplete_tasks = dataMan().get_todo_items(guild_id=guild_id, filter_for='incompleted')
        completed_tasks = livetasks.filter_out_old_completed_tasks(
            task_list=dataMan().get_todo_items(
                guild_id=guild_id,
                filter_for='completed',
            )
        )

        embed = livetasks.gen_livetasklist_embed(completed_tasks, incomplete_tasks)

        if embed is False:
            return False

        if target_user_id is not None:
            pm_channel = await plugin.bot.rest.create_dm_channel(target_user_id)
            try:
                await pm_channel.send(embed=embed)
            except hikari.errors.NotFoundError:
                return False
            except hikari.errors.ForbiddenError:
                return False
            except hikari.errors.BadRequestError:
                return False
        else:
            try:
                await plugin.bot.rest.create_message(embed=embed, channel=target_channel_id)
            except hikari.errors.NotFoundError:
                logging.info(f"Target channel for guild {guild_id} not found. Disabling live task list.")
                return False

    @staticmethod
    async def update_for_guild(guild_id):
        incomplete_tasks = dataMan().get_todo_items(guild_id=int(guild_id), filter_for='incompleted')
        unfiltered_completed_tasks = dataMan().get_todo_items(guild_id=int(guild_id), filter_for='completed')
        task_channel = dataMan().get_taskchannel(int(guild_id))

        if task_channel is None:
            return False

        # Filters out completed tasks that have been completed for more than 7 days
        # This is to prevent the list from getting too long.
        completed_tasks = livetasks.filter_out_old_completed_tasks(unfiltered_completed_tasks)

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
            for single_embed in embed:
                await plugin.bot.rest.create_message(embed=single_embed, channel=task_channel)
        except hikari.errors.NotFoundError:
            logging.info(f"Task channel for guild {guild_id} not found. Disabling live task list.")
            dataMan().clear_taskchannel(guild_id)
            return False

        return True

    @staticmethod
    def gen_livetasklist_embed(completed_tasks, incomplete_tasks):
        if len(completed_tasks) + len(incomplete_tasks) == 0:
            return [hikari.Embed(  # <- Return a list even when empty
                title="Live Task List",
                description="Unfortunately, there are no tasks incomplete or complete to display.",
                color=0x00ff00
            )]

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

        custom_desc = dataMan().get_livelist_description(guild_id)

        # New Embed Creation for when too much text
        def create_new_embed():
            new_embed = hikari.Embed(
                title="Live Task List",
                description=f"{style} style",
                color=0x00ff00
            ).add_field(
                name="Information",
                value=f"{custom_desc}\n\n" if custom_desc is not None else "This is a live list of incomplete and newly completed tasks.\nThe details of {len(incomplete_tasks)} incomplete task(s) is attached below.\n\n"
            )
            return new_embed

        embeds = [create_new_embed()]
        current_embed = embeds[-1]

        # Sort tasks
        incomplete_tasks.sort(key=lambda task: task[8] is not None and task[8] != "")
        completed_tasks.sort(key=lambda task: task[8] is not None and task[8] != "")

        batch_id = random.randint(1000000000, 9999999999)

        failed_compile_count = 0
        failed_compile_ids = []

        # Helper to get the current embed size
        def embed_total_length(embed):
            length = len(embed.title or "") + len(embed.description or "")
            for field in embed.fields:
                length += len(field.name or "") + len(field.value or "")
            return length

        def safe_add_task(task):
            """
            Turns out that adding tasks to an embed without going over 6000 characters is a pain.
            This function makes it less pain :>
            """
            nonlocal current_embed
            nonlocal batch_id  # keep using it

            # 1. Generate the text FIRST
            preview_embed = livetasks.add_task_field(task, current_embed, style, batch_id, dry_run=True)

            # 2. Calculate size if added
            future_size = embed_total_length(current_embed) + len(preview_embed)

            # 3. If the future size exceeds 6000, start a new embed
            if future_size > 6000:
                current_embed = create_new_embed()
                embeds.append(current_embed)
                batch_id = random.randint(1000000000, 9999999999)
                plugin.bot.d[f'batch-{batch_id}'] = {'current_page': 1}
                current_embed.add_field(name="Details Page 1", value="", inline=False)

            # 4. Actually add a task for real now
            addition = livetasks.add_task_field(task, current_embed, style, batch_id)
            if addition is False:
                return False
            return addition

        # Add completed tasks
        for task in completed_tasks:
            if safe_add_task(task) is False:
                failed_compile_count += 1
                failed_compile_ids.append(task[3])

        # Add incomplete tasks
        category_sorted_tasks = {}
        for task in incomplete_tasks:
            category = task[8] or ""
            if category not in category_sorted_tasks:
                category_sorted_tasks[category] = []
            category_sorted_tasks[category].append(task)

        for category in sorted(category_sorted_tasks.keys(), key=lambda x: x != ""):
            for task in category_sorted_tasks[category]:
                if safe_add_task(task) is False:
                    failed_compile_count += 1
                    failed_compile_ids.append(task[3])

        # Add failure info if needed
        if failed_compile_count != 0:
            failed_text = (
                f"While trying to compile this list, {failed_compile_count} task(s) could not compile.\n"
                f"Couldn't compile Tasks with IDs: {', '.join(map(str, failed_compile_ids))}"
            )
            if embed_total_length(current_embed) + len(failed_text) > 6000:
                current_embed = create_new_embed()
                embeds.append(current_embed)
            current_embed.add_field(
                name="Tasks could not compile",
                value=failed_text
            )
            logging.warning(
                f"Tried to compile some tasks for guild {guild_id} but {failed_compile_count} tasks couldn't compile. Please debug.\n"
                f"Problematic ID(s)/v: {failed_compile_ids}")

        # Clean up: remove any totally empty fields
        for embed in embeds:
            field_id = 0
            for field in embed.fields:
                if len(field.value) == 0:
                    embed.remove_field(field_id)
                field_id += 1

        total_pages = len(embeds)
        for idx, embed in enumerate(embeds, start=1):
            embed.set_footer(text=f"Page {idx} of {total_pages}")

        return embeds

    @staticmethod
    def add_task_field(task: tuple, embed, style, batch_id: int, dry_run=False):
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
            if isinstance(cached_status, bool) and (datetime.now() - cached_time) < CACHE_EXPIRATION_TIME:
                show_x = cached_status
            else:
                show_x = bool(dataMan().get_show_task_completion(guild_id))
                plugin.bot.d['show_x_cache'][int(guild_id)] = {
                    'status': show_x,
                    'timenow': datetime.now()
                }
        else:
            show_x = bool(dataMan().get_show_task_completion(guild_id))
            plugin.bot.d['show_x_cache'][int(guild_id)] = {
                'status': show_x,
                'timenow': datetime.now()
            }

        if show_x is False and not completed:
            completed_text = ""

        if task_desc == "...":
            task_desc = ""

        contributors = dataMan().get_contributors(task_id=identifier)
        assigned_user = dataMan().get_task_incharge(task_id=identifier)
        custom_live_text = dataMan().get_livelist_format(guild_id)

        deadline_txt = ""
        if not completed and deadline is not None:
            try:
                deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
                if deadline < datetime.now():
                    deadline_txt += f"⚠️ Deadline expired <t:{int(deadline.timestamp())}:R>!\n"
                else:
                    deadline_txt += f"Deadline: {deadline.strftime('%d/%m/%Y %I:%M %p')}\n"
                    deadline_txt += f"Time left: <t:{int(deadline.timestamp())}:R>\n\n"
            except Exception as err:
                logging.error(f"Deadline formatting error for task {identifier}: {err}")
                return False

        # Build the text segment we want to add

        q_or_s = '"' if len(task_desc) > 0 else ''
        segment = ""

        # Add category heading if not already present
        if category:
            segment += f"**__{category}__**\n" if style in ['pinned', 'compact', 'minimal', 'pinned-minimal'] else f"-- **__{category}__** --\n\n"

        if custom_live_text is None:
            if style == 'classic':
                segment += f"{task_name}\n(ID: {identifier})\n{task_desc}\n{completed_text}\nAdded by: <@{added_by}>\n{len(contributors)} helping\n"
                if assigned_user:
                    segment += f"Assigned to <@{assigned_user}>\n"
                if deadline_txt:
                    segment += f"{deadline_txt}\n"
            elif style == 'minimal':
                segment += f"({identifier}) {' ' if show_x else ''}{completed_text} {task_name}\n"
                if deadline_txt:
                    segment += f"{deadline_txt}\n"
            elif style == 'pinned':
                segment += f"- ({identifier}) {task_name} {' ' if show_x else ''}{completed_text}\n{q_or_s}{task_desc}{q_or_s} {len(contributors)} people helping.\nAdded by <@{added_by}>\n"
                if assigned_user:
                    segment += f"Assigned to <@{assigned_user}>\n"
                if deadline_txt:
                    segment += f"{deadline_txt}\n"
            elif style == 'pinned-minimal':
                segment += f"- ({identifier}) {' ' if show_x else ''}{completed_text} {task_name}\n"
            elif style == 'compact':
                segment += f"({identifier}) {task_name} {completed_text} {' ' if show_x else ''}{q_or_s}{task_desc}{q_or_s} {len(contributors)} helping. <@{added_by}>\n"
                if deadline_txt:
                    segment += f"{deadline_txt}\n"
            else:
                raise ValueError("Invalid style")
        else:
            segment += f"{parse_livelist_format(custom_live_text, task_id=identifier)}\n"
            if deadline_txt:
                segment += f"{deadline_txt}\n"

        # Now deal with embed and fields safely under 1024 characters

        key = f"batch-{batch_id}"
        if plugin.bot.d.get(key) is None:
            plugin.bot.d[key] = {'current_page': 1}
            embed.add_field(name="Details Page 1", value="", inline=False)

        page_no = plugin.bot.d[key]['current_page']
        field = embed.fields[page_no]

        # If adding this segment overflows, move to the next page
        if len(field.value) + len(segment) > 1024:
            page_no += 1
            plugin.bot.d[key]['current_page'] = page_no
            embed.add_field(name=f"Details Page {page_no}", value="", inline=False)
            field = embed.fields[page_no]

        if dry_run:
            return segment  # Return the text that would be added

        # Append safely
        new_value = field.value + segment
        embed.edit_field(
            page_no,
            field.name,
            new_value,
            inline=False
        )

        return embed

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
