from library.storage import dataMan
from library.perms import perms
import hikari
import miru
import io

class view_cmd_view:
    def __init__(self, task_id, guild_id):
        self.task_id = task_id
        if str(task_id).isnumeric() is False: # Not an ID, but a name.
            # Find the name
            tasks = dataMan().get_todo_items(filter_for="*", identifier=task_id, guild_id=guild_id)
            if len(tasks) > 1:
                raise IndexError("Too many tasks to search by name!")
            else:
                self.task_id = tasks[0][3]

        self.guild_id = guild_id
        self.task_list = self.update_task_list()

    def update_task_list(self):
        try:
            filter_for = 'incompleted' if not self.task_id.isnumeric() else "*"
        except AttributeError:
            filter_for = '*'

        task_list = dataMan().get_todo_items(
            guild_id=self.guild_id,
            identifier=self.task_id,
            filter_for=filter_for
        )
        self.task_list = task_list
        return task_list

    def generate_task_embed(self, author_id):
        task_list = self.update_task_list()

        task_count = len(task_list)
        if task_count != 1:
            desc_value = f"We found {task_count} tasks that meet the requested criteria."
        else:
            desc_value = None

        embed = (
            hikari.Embed(
                title="Found Tasks",
                description=desc_value,
            )
        )

        attachment = None
        task_counter = 0
        for task in task_list:  # There should be only 1 task.
            name = task[0]
            description = task[1]
            completed = task[2]
            task_id = task[3]
            added_by = task[5]
            category = task[8]

            if category is not None:
                name = f"**{category}**"

            completed_text = "Completed: " + ('❌' if not completed else '✅')

            # Trunciate description if too long.
            if len(description) > 800:
                description_file = io.BytesIO(description.encode("utf-8"))
                description = description[:800] + "... (trunciated to file)"

                # Generates a description text file using io
                attachment = hikari.Bytes(description_file, 'description.txt')

            desc_value = f"{description}\n\n{completed_text}" if description != "..." else completed_text
            desc_value += f"\nAdded by: <@{added_by}>"

            is_contributing = int(author_id) in dataMan().get_contributors(task_id)
            if is_contributing:
                if not completed:
                    desc_value += f"\nViewer is contributing to this task."
                else:
                    desc_value += f"\nViewer has contributed to this task."
            else:
                if not completed:
                    desc_value += f"\nViewer is not contributing to this task."
                else:
                    desc_value += f"\nViewer did not contribute to this task."

            task_counter += 1
            embed.add_field(
                name=f'{task_counter}. {name}\n(ID: {task_id})',
                value=desc_value,
                inline=False
            )

        return {
            "embed": embed,
            "task_c": task_counter,
            "attached": attachment
        }

    # TODO: Fix the bug where if you run the view and the permissions change for who can interact with tasks, it still allows you to interact
    # noinspection PyMethodParameters
    async def init_view(viewself, user_id) -> miru.view:
        task_id = viewself.task_id
        dm = dataMan()

        buttons_disabled:bool = not await perms().can_interact_tasks(viewself.guild_id, user_id=user_id)

        # noinspection PyUnusedLocal
        class mainview(miru.View):
            # Define a new Button with the Style of success (Green)
            @miru.button(label="Toggle helping", style=hikari.ButtonStyle.SUCCESS, disabled=buttons_disabled)
            async def tgl_helping_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                contributors = dm.get_contributors(task_id=int(task_id))
                if not ctx.author.id in contributors:
                    contributing = False
                else:
                    contributing = True

                if not contributing:
                    result = dm.mark_user_as_contributing(int(ctx.author.id), guild_id=int(ctx.guild_id), task_id=int(task_id))
                    if result == -2:
                        embed = viewself.generate_task_embed(int(ctx.author.id))
                        await ctx.edit_response(
                            embed=embed['embed'].add_field(
                                name="Late contribution",
                                value="You cannot contribute to a task that's already done."
                            ),
                            attachment=embed['attached']
                        )
                        return
                    embed = viewself.generate_task_embed(int(ctx.author.id))
                    await ctx.edit_response(
                        embed=embed['embed'],
                        attachment=embed['attached']
                    )
                else:
                    dm.remove_contributor(task_id=int(task_id), user_id=int(ctx.author.id), guild_id=ctx.guild_id)
                    embed = viewself.generate_task_embed(int(ctx.author.id))
                    await ctx.edit_response(
                        embed=embed['embed'],
                        attachment=embed['attached']
                    )

            @miru.button(label="Toggle Done", style=hikari.ButtonStyle.SUCCESS, disabled=buttons_disabled)
            async def tgl_done_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                completed = dm.get_is_task_completed(task_id_or_name=task_id)

                if not completed:
                    dm.mark_todo_finished(name_or_id=task_id, guild_id=int(ctx.guild_id))
                    embed = viewself.generate_task_embed(int(ctx.author.id))
                    await ctx.edit_response(
                        embed=embed['embed'],
                        attachment=embed['attached']
                    )
                else:
                    dm.mark_todo_not_finished(name_or_id=task_id, guild_id=int(ctx.guild_id))
                    embed = viewself.generate_task_embed(int(ctx.author.id))
                    await ctx.edit_response(
                        embed=embed['embed'],
                        attachment=embed['attached']
                    )

            # Define a new Button that when pressed will stop the view
            # and invalidate all the buttons in this view
            @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER, disabled=False)  # Exit button always enabled.
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                embed = viewself.generate_task_embed(int(ctx.author.id))
                await ctx.edit_response(
                    embed=embed['embed'],
                    attachment=None,
                    components=[]
                )
                self.stop()  # Called to stop the view

        return mainview()
