from library.storage import dataMan
import hikari
import miru

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

        task_counter = 0
        for task in task_list:
            name = task[0]
            description = task[1]
            completed = task[2]
            task_id = task[3]
            added_by = task[5]
            category = task[8]

            if category is not None:
                name = f"**{category}**"

            completed_text = "Completed: " + ('❌' if not completed else '✅')
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

        return embed, task_counter

    # noinspection PyMethodParameters
    def init_view(viewself) -> miru.view:
        task_id = viewself.task_id
        dm = dataMan()

        # noinspection PyUnusedLocal
        class mainview(miru.View):
            # Define a new Button with the Style of success (Green)
            @miru.button(label="Toggle helping", style=hikari.ButtonStyle.SUCCESS)
            async def tgl_helping_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                contributors = dm.get_contributors(task_id=int(task_id))
                if not ctx.author.id in contributors:
                    contributing = False
                else:
                    contributing = True

                if not contributing:
                    dm.mark_user_as_contributing(int(ctx.author.id), guild_id=int(ctx.guild_id), task_id=int(task_id))
                    embed = viewself.generate_task_embed(int(ctx.author.id))[0]
                    await ctx.edit_response(
                        embed=embed
                    )
                else:
                    dm.remove_contributor(task_id=int(task_id), user_id=int(ctx.author.id))
                    embed = viewself.generate_task_embed(int(ctx.author.id))[0]
                    await ctx.edit_response(
                        embed=embed
                    )

            @miru.button(label="Toggle Done", style=hikari.ButtonStyle.SUCCESS)
            async def tgl_done_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                completed = dm.get_is_task_completed(task_id_or_name=task_id)

                if not completed:
                    dm.mark_todo_finished(name_or_id=task_id, guild_id=int(ctx.guild_id))
                    embed = viewself.generate_task_embed(int(ctx.author.id))[0]
                    await ctx.edit_response(
                        embed=embed
                    )
                else:
                    dm.mark_todo_not_finished(name_or_id=task_id, guild_id=int(ctx.guild_id))
                    embed = viewself.generate_task_embed(int(ctx.author.id))[0]
                    await ctx.edit_response(
                        embed=embed
                    )

            # Define a new Button that when pressed will stop the view
            # & invalidate all the buttons in this view
            @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                self.stop()  # Called to stop the view

        return mainview()