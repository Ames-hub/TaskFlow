from library.storage import dataMan, sqlite_storage
from library.live_task_channel import livetasks
from library.botapp import miru_client, botapp
from library import tferror
import datetime
import hikari
import miru


def init_edit_modal(task_id):
    class Edit_modal(miru.Modal, title="Modify a task, leave blank to keep unchanged."):
        new_name = miru.TextInput(
            label="Name",
            placeholder="What's the new name of the task?",
            required=False,
            style=hikari.TextInputStyle.SHORT,
            max_length=botapp.d['max_name_length'],
        )
        new_desc = miru.TextInput(
            label="Description",
            placeholder="What's the new description?",
            required=False,
            style=hikari.TextInputStyle.PARAGRAPH,
            max_length=botapp.d['max_desc_length'],
        )
        new_category = miru.TextInput(
            label="Category",
            placeholder="To what category does this task now belong?",
            required=False,
            style=hikari.TextInputStyle.SHORT
        )
        new_deadline = miru.TextInput(
            label="Deadline",
            placeholder="What's the deadline? (YYYY-MM-DD HH:MM AM/PM)",
            required=False,
            style=hikari.TextInputStyle.SHORT
        )

        # TODO: Make deadline modifiable

        # The callback function is called after the user hits 'Submit'
        async def callback(self, ctx: miru.ModalContext) -> None:
            task_name = self.new_name.value
            task_desc = self.new_desc.value

            if task_name == "*":
                embed = hikari.Embed(
                    title="Task name cannot be '*'",
                    description="You can't name your task '*'. That's reserved."
                )
                await ctx.respond(embed)
                return
            elif len(task_name) > botapp.d['max_name_length']:
                embed = hikari.Embed(
                    title="Task name too long!",
                    description=f"Task names cannot be longer than {botapp.d['max_name_length']} characters."
                )
                await ctx.respond(embed)
                return
            if len(task_desc) > botapp.d['max_desc_length']:
                embed = hikari.Embed(
                    title="Task description too long!",
                    description=f"Task descriptions cannot be longer than {botapp.d['max_desc_length']} characters."
                )
                await ctx.respond(embed)
                return

            try:
                deadline = datetime.datetime.strptime(self.new_deadline.value, '%Y-%m-%d %I:%M %p') if self.new_deadline.value else None
            except ValueError:
                embed = hikari.Embed(
                    title="Invalid deadline format!",
                    description="Please use the format 'YYYY-MM-DD HH:MM AM/PM' for the deadline. For example, '2024-12-31 05:30 PM'.\n"
                    "If you don't want to set a deadline, leave the field blank."
                )
                await ctx.respond(embed)
                return

            dataMan().set_new_task_data(
                task_id=task_id,
                task_name=task_name,
                task_desc=task_desc,
                task_category=self.new_category.value,
                task_deadline=deadline
            )

            await ctx.respond(
                embed=(
                    hikari.Embed(
                        title="Task edited!",
                        description="Your task was successfully edited."
                    )
                ),
                components=[]
            )

            await livetasks.update_for_guild(int(ctx.guild_id))

    return Edit_modal()

class main_view:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.task_data = self.get_task_data()
        self.task_data_options = self.gen_task_options()

    def get_task_data(self):
        return dataMan().get_todo_items(only_keys=['id', 'name', 'description', 'completed'], guild_id=int(self.guild_id), filter_for='*')

    def gen_init_embed(self):
        task_list = ""

        # Tests to see how long the descriptions are and if they should be included in the embed
        total_length_trunciated = 0
        for task in self.task_data:
            task_desc = self.task_data[task]['description']
            if len(task_desc) > 400:
                task_desc = task_desc[:400] + "... (trunciated)"

            total_length_trunciated += len(task_desc)

        include_desc = True
        if total_length_trunciated > 600:
            include_desc = False

        for task in self.task_data:
            task = self.task_data[task]
            completed_text = '❌' if not task["completed"] else '✅'
            q_or_s = "'" if len(task['description']) > 0 else ""
            if not include_desc:
                q_or_s = ""
            if len(task['description']) > 100:
                task['description'] = task['description'][:100] + "... (trunciated)"
            task_list += f"({str(task['id'])}) {task['name']} {q_or_s}{task['description'] if include_desc else ""}{q_or_s} {completed_text}\n"

        return (
            hikari.Embed(
                description="The server's task list"
            )
            .add_field(
                name="Global tasks",
                value=task_list
            )
        )

    def gen_task_options(self):
        tasks_data_options = []
        if len(self.task_data) == 0:
            return -1
        if len(self.task_data) <= 25:
            for task_id, task in self.task_data.items():
                tasks_data_options.append(
                    miru.SelectOption(
                        label=f"({task['id']}) {task['name']}",
                        value=str(task['id'])
                    )
                )

        self.task_data_options = tasks_data_options
        return tasks_data_options

    # noinspection PyMethodParameters
    def init_view(viewself):
        """
        Make sure to use keys_only=['id', 'name']).values() for tasks_data
        """

        # Checks that tasks do in fact exist to be edited.
        count = sqlite_storage.count_tasks(guild_id=viewself.guild_id)
        if count <= 0:
            raise tferror.no_tasks()

        # noinspection PyUnusedLocal
        class Menu_Init(miru.View):
            # noinspection PyUnusedLocal
            @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER, row=2)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(
                    hikari.Embed(
                        title="Exiting menu.",
                        description="Goodbye!",
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            @miru.text_select(options=viewself.task_data_options, placeholder="Edit Task")
            async def select_task_to_edit(self, ctx: miru.ViewContext, select: miru.TextSelect):
                task_id = select.values[0]

                modal = init_edit_modal(task_id)
                builder = modal.build_response(miru_client)
                await builder.create_modal_response(ctx.interaction)
                miru_client.start_modal(modal)

        return Menu_Init()