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

        custom_desc = dataMan().get_livelist_description(guild_id)

        embed = hikari.Embed(
            title="Live Task List",
            description=f"{style} style",
            color=0x00ff00
        ).add_field(
            name="Details",
            value=f"{custom_desc}\n\n" if custom_desc is not None else "This is a live list of incomplete and newly completed tasks.\n"
                  f"The details of {len(incomplete_tasks)} incomplete task(s) is attached below.\n\n"
        )

        # Sort tasks: prioritize tasks without a category
        incomplete_tasks.sort(key=lambda task: task[8] is not None and task[8] != "")
        completed_tasks.sort(key=lambda task: task[8] is not None and task[8] != "")

        # A system Batch ID used to keep track of pages in the embed
        batch_id = random.randint(1000000000, 9999999999)

        # Add completed tasks to the embed
        failed_compile_count = 0
        failed_compile_ids = []
        for task in completed_tasks:
            addition = livetasks.add_task_field(task, embed, style, batch_id)
            if addition is False:
                failed_compile_count =+ 1
                failed_compile_ids.append(task[3])
                continue
            else:
                embed = addition

        # Categorise remaining incomplete tasks
        category_sorted_tasks = {}
        for task in incomplete_tasks:
            category = task[8] or ""  # Empty category comes first
            if category not in category_sorted_tasks:
                category_sorted_tasks[category] = []
            category_sorted_tasks[category].append(task)

        # Add sorted tasks to the embed
        for category in sorted(category_sorted_tasks.keys(), key=lambda x: x != ""):
            for task in category_sorted_tasks[category]:
                addition = livetasks.add_task_field(task, embed, style, batch_id)
                if addition is False:
                    failed_compile_count =+ 1
                    failed_compile_ids.append(task[3])
                    continue
                else:
                    embed = addition

        if failed_compile_count != 0:
            failed_compile_ids_str = []
            for uuid in failed_compile_ids:
                failed_compile_ids_str.append(str(uuid))
            embed.add_field(
                name="Tasks could not compile",
                value=f"While trying to compile this list, {failed_compile_count} task(s) could not compile.\n"
                      "Check their data, is anything especially unusual?\nRegardless, Maintainers have been alerted.\n"
                      f"Couldn't compile Tasks with IDs: {", ".join(failed_compile_ids_str)}"
            )
            logging.warning(f"Tried to compile some tasks for guild {guild_id} but {failed_compile_count} tasks couldn't compile. Please debug.\n"
                            f"Problematic ID(s)/v: {failed_compile_ids}")

        return embed

    @staticmethod
    def add_task_field(task:tuple, embed, style, batch_id:int):
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
                    try:
                        deadline_txt += f"Deadline: {deadline.strftime("%d/%m/%Y %I:%M %p")}\n"
                    except OSError:
                        deadline_txt += "Deadline is too far in the future to display!\n"
                    except Exception as err:
                        logging.error(f"Something's wrong with converting deadline date to strftime for task id {identifier}\n"
                                      f"Deadline: {deadline}, type: {type(deadline)} ", err)
                        return False

                    try:
                        deadline_txt += f"Time left: <t:{int(deadline.timestamp())}:R>\n\n"
                    except OSError:
                        # Handles if someone tries to put in like, year 9999
                        deadline_txt += "A POSIX timestamp can't go that far in the future!\n\n"
                    except Exception as err:
                        logging.error(f"Something's wrong with converting deadline date to timestamp for task id {identifier}\n"
                                      f"Deadline: {deadline}, type: {type(deadline)} ", err)
                        return False

        # Ensures >1024 letters do not go on 1 page
        page_no = 0
        page_threshold = 900
        amount_added = len(task_name) + len(task_desc) + len(deadline_txt) + len(completed_text) + len(f"<@{added_by}>") + len(contributors)
        # If amount_added is > 1024, we cannot add it. Period.
        if amount_added > page_threshold:
            return False

        if plugin.bot.d.get(f'batch-{batch_id}', None) is None:
            # If it doesn't exist, make it.
            plugin.bot.d[f'batch-{batch_id}'] = {}
            plugin.bot.d[f'batch-{batch_id}'][page_no] = amount_added
            plugin.bot.d[f'batch-{batch_id}']['current_page'] = 0
        else:
            # The page must have been saved, so we retrieve it.
            page_no = plugin.bot.d[f'batch-{batch_id}']['current_page']
            # Else, add the total. Increment page if needed.
            if plugin.bot.d[f'batch-{batch_id}'][page_no] + amount_added > page_threshold:
                page_no += 1
                plugin.bot.d[f'batch-{batch_id}']['current_page'] = page_no
                plugin.bot.d[f'batch-{batch_id}'][page_no] = 0
                # Creates a new embed field for the page
                embed.add_field(
                    name=f"Details (p{page_no})",
                    value="",
                    inline=False
                )
            plugin.bot.d[f'batch-{batch_id}'][page_no] += amount_added

        efield = embed.fields[page_no].value

        if category is not None and category != "":
            if style in ['classic']:
                if f"-- **__{category}__** --" not in efield:
                    efield += f"\n-- **__{category}__** --\n\n"
            elif style in ['pinned', 'pinned-minimal', 'minimal', 'compact']:
                if f"# {category}" not in efield:
                    efield += f"**__{category}__**\n"

        custom_live_text = dataMan().get_livelist_format(guild_id)
        assigned_user = dataMan().get_task_incharge(task_id=identifier)

        if custom_live_text is None:
            # Quote or space
            q_or_s = '"' if len(task_desc) > 0 else ''

            if style == 'classic':
                efield += f"{task_name}\n"
                efield += f"(ID: {identifier})\n"
                efield +=  f"{task_desc}{"\n" if len(task_desc) != 0 else ""}"
                efield += f"{completed_text}{"\n" if show_x else ""}"
                efield += f"Added by: <@{added_by}>\n"
                efield += f"{len(contributors)} helping\n"

                if assigned_user is not None:
                    efield += f"Assigned to <@{assigned_user}>\n{"\n" if len(deadline_txt) == 0 else ""}"
                if len(deadline_txt) > 0:
                    # Checks if the last character is a newline
                    is_newline = efield[-1] == "\n"
                    efield += f"{deadline_txt}{"\n\n" if not is_newline else ""}"

            elif style == 'minimal':
                efield = efield + f"({identifier}){" " if show_x else ""}{completed_text} {task_name}\n{"\n" if len(deadline_txt) == 0 else ""}"
                if len(deadline_txt) > 0:
                    efield = efield + f"{deadline_txt}\n\n"
            elif style == 'pinned':
                efield += f"- ({identifier}) {task_name}{" " if show_x else ""}{completed_text}\n"
                efield += f"{q_or_s}{task_desc}{q_or_s} {len(contributors)} people helping.\n"
                efield += f"Added by <@{added_by}>\n"

                if assigned_user is not None:
                    efield += f"Assigned to <@{assigned_user}>\n{"\n" if len(deadline_txt) == 0 else ""}"
                if len(deadline_txt) > 0:
                    # Checks if the last character is a newline
                    is_newline = efield[-1] == "\n"
                    efield += f"{deadline_txt}{"\n\n" if not is_newline else ""}"
            elif style == 'pinned-minimal':
                efield = efield + f"- ({identifier}){" " if show_x else ""}{completed_text} {task_name}\n\n"
            elif style == 'compact':
                efield = efield + f"({identifier}) {task_name} {completed_text}{" " if show_x else ""}{q_or_s}{task_desc}{q_or_s} {len(contributors)} helping. <@{added_by}>\n"
                if len(deadline_txt) > 0:
                    efield += f"{deadline_txt}\n\n"
            else:
                raise ValueError("Invalid style")
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
