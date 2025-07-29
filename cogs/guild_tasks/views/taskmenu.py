from library.live_task_channel import livetasks
from library.botapp import miru_client, botapp
from library.parsing import parse_deadline
from library.storage import dataMan
import datetime
import hikari
import miru

class views:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.task_data = self.get_task_data()

    def get_task_data(self):
        return dataMan().get_todo_items(only_keys=['id', 'name', 'description', 'completed'], guild_id=int(self.guild_id), filter_for='*')

    def gen_init_embed(self):
        task_list = ""
        self.task_data = self.get_task_data()
        for task in self.task_data:
            task = self.task_data[task]
            completed_text = '❌' if not task["completed"] else '✅'
            description = task['description']
            if len(description) > 100:
                description = description[:57] + "..."
            task_name = task['name']
            if len(task_name) > 60:
                task_name = task_name[:57] + "..."
            q_or_s = "'" if len(description) > 0 else ""
            task_list += f"({str(task['id'])}) {task_name} {q_or_s}{description}{q_or_s} {completed_text}\n"

        if len(task_list) > 1024:
            task_list = task_list[:985] + "... (This list is too long to display)"

        return (
            hikari.Embed(
                description="The server's task list"
            )
            .add_field(
                name="Global tasks",
                value=task_list
            )
        )

    # noinspection PyMethodParameters
    def init_view(viewself):
        """
        Make sure to use keys_only=['id', 'name']).values() for tasks_data
        """
        tasks_data_options = []
        if len(viewself.task_data) == 0:
            return -1
        for task_id, task in viewself.task_data.items():
            tasks_data_options.append(
                miru.SelectOption(
                    label=f"({task['id']}) {task['name']}",
                    value=str(task['id'])
                )
            )

        # noinspection PyUnusedLocal
        class Menu_Init(miru.View):
            # noinspection PyMethodParameters
            @miru.text_select(
                placeholder="Toggle",
                options=tasks_data_options,
            )
            async def task_select(_, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
                task_id = select.values[0]
                dm = dataMan()

                # Gets if it's completed or not
                task_done = dm.get_is_task_completed(task_id_or_name=task_id)

                if task_done is False:
                    dm.mark_todo_finished(name_or_id=task_id, guild_id=viewself.guild_id)
                else:
                    dm.mark_todo_not_finished(name_or_id=task_id, guild_id=viewself.guild_id)

                await livetasks.update_for_guild(int(ctx.guild_id))
                await ctx.edit_response(viewself.gen_init_embed())

            # noinspection PyUnusedLocal
            @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(
                    hikari.Embed(
                        title="Exitting menu.",
                        description="Have any suggestions? Be sure to let us know on the github!",
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            @miru.button(label="List", style=hikari.ButtonStyle.SUCCESS, emoji="📋")
            async def task_list_view_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(viewself.gen_init_embed())

            @miru.button(label="Add", style=hikari.ButtonStyle.SUCCESS, emoji="➕")
            async def add_task_btn(self, ctx: miru.ViewContext, button: miru.Button):
                class MyModal(miru.Modal, title="Create a task"):

                    name = miru.TextInput(
                        label="Task",
                        placeholder="What's the name of the task?",
                        required=True,
                        style=hikari.TextInputStyle.SHORT
                    )

                    desc = miru.TextInput(
                        label="Description",
                        required=False,
                        placeholder="How would you describe the task?",
                        style=hikari.TextInputStyle.PARAGRAPH
                    )

                    category = miru.TextInput(
                        label="Category",
                        placeholder="To what category does this task belong?",
                        required=False,
                        style=hikari.TextInputStyle.SHORT
                    )

                    deadline_dmy = miru.TextInput(
                        label="Due Date",
                        placeholder="DD/MM/YYYY, eg \"13/03/2025\"",
                        required=False,
                        style=hikari.TextInputStyle.SHORT
                    )

                    deadline_hm = miru.TextInput(
                        label="Due Time",
                        placeholder="Format: HH:MM AM/PM, eg \"12:44 PM\"",
                        required=False,
                        style=hikari.TextInputStyle.SHORT
                    )

                    # The callback function is called after the user hits 'Submit'
                    async def callback(self, ctx: miru.ModalContext) -> None:
                        deadline_obj = parse_deadline(
                            deadline_date=self.deadline_dmy.value,
                            deadline_hmp=self.deadline_hm.value
                        )

                        if type(deadline_obj) != datetime.datetime:
                            await ctx.edit_response(
                                embed=(
                                    hikari.Embed(
                                        title="Could not read Deadline",
                                        description=str(deadline_obj)  # It'll be the error message if it's not a datetime obj
                                    )
                                )
                            )
                            return

                        task_name = str(self.name.value)
                        task_desc = str(self.desc.value)

                        if task_name == "*":
                            await ctx.edit_response(
                                embed=(
                                    hikari.Embed(
                                        title="Task name cannot be '*'",
                                        description="You can't name your task '*'. That's reserved."
                                    )
                                )
                            )
                        elif len(task_name) > botapp.d['max_name_length']:
                            await ctx.edit_response(
                                embed=(
                                    hikari.Embed(
                                        title="Task name too long!",
                                        description=f"Task names cannot be longer than {botapp.d['max_name_length']} characters."
                                    )
                                )
                            )
                            return
                        if len(task_desc) > botapp.d['max_desc_length']:
                            await ctx.edit_response(
                                embed=(
                                    hikari.Embed(
                                        title="Task description too long!",
                                        description=f"Task descriptions cannot be longer than {botapp.d['max_desc_length']} characters."
                                    )
                                )
                            )

                        dataMan().add_todo_item(
                            added_by=ctx.author.id,
                            name=task_name,
                            description=task_desc,
                            guild_id=ctx.guild_id,
                            category=self.category.value,
                            deadline=deadline_obj
                        )
                        await ctx.edit_response(
                            embed=(
                                hikari.Embed(
                                    title="Task created!",
                                    description="Your task was successfully created."
                                )
                            )
                        )
                        await livetasks.update_for_guild(int(ctx.guild_id))

                modal = MyModal()
                builder = modal.build_response(miru_client)

                await builder.create_modal_response(ctx.interaction)

                miru_client.start_modal(modal)

        return Menu_Init()