from library.botapp import miru_client
from library.storage import dataMan
import hikari
import miru

class main_view:
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
            q_or_s = "'" if len(task['description']) > 0 else ""
            task_list += f"({str(task['id'])}) {task['name']} {q_or_s}{task['description']}{q_or_s} {completed_text}\n"

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
            # noinspection PyUnusedLocal
            @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER, row=2)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(
                    hikari.Embed(
                        title="Exitting menu.",
                        description="Have any suggestions? Be sure to let us know on the github!",
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            @miru.text_select(options=tasks_data_options, placeholder="Edit Task")
            async def select_task_to_edit(self, ctx: miru.ViewContext, select: miru.TextSelect):
                task_id = select.values[0]
                class MyModal(miru.Modal, title="Modify a task, leave blank to keep unchanged."):
                    new_name = miru.TextInput(
                        label="Name",
                        placeholder="What's the new name of the task?",
                        required=False,
                        style=hikari.TextInputStyle.SHORT
                    )
                    new_desc = miru.TextInput(
                        label="Description",
                        placeholder="What's the new description?",
                        required=False,
                        style=hikari.TextInputStyle.SHORT
                    )
                    new_category = miru.TextInput(
                        label="Category",
                        placeholder="To what category does this task now belong?",
                        required=False,
                        style=hikari.TextInputStyle.SHORT
                    )
                    # TODO: Make deadline modifiable

                    # The callback function is called after the user hits 'Submit'
                    async def callback(self, ctx: miru.ModalContext) -> None:
                        dataMan().set_new_task_data(
                            task_id=task_id,
                            task_name=self.new_name.value,
                            task_desc=self.new_desc.value,
                            task_category=self.new_category.value
                        )
                        await ctx.edit_response(
                            embed=viewself.gen_init_embed(),
                        )

                modal = MyModal()
                builder = modal.build_response(miru_client)

                await builder.create_modal_response(ctx.interaction)

                miru_client.start_modal(modal)

        return Menu_Init()