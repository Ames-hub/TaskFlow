from library.botapp import miru_client, botapp
from library.parsing import parse_deadline
from library.storage import dataMan
import hikari
import miru


class main_view:
    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def gen_initial_embed(self):
        return (
            hikari.Embed(
                title="Templates",
                description="A Template is a preset task that is used for recurring tasks.\n"
                            "Please click the button below to begin making one."
            )
        )

    def init_view(self):
        class Menu_Init(miru.View):
            # noinspection PyUnusedLocal
            @miru.button(label="Cancel", style=hikari.ButtonStyle.DANGER)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(
                    hikari.Embed(
                        title="Exitting menu.",
                        description="Have any suggestions? Be sure to let us know on the github!",
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            # noinspection PyUnusedLocal
            @miru.button(label="Create Template")
            async def report_btn(self, ctx: miru.ViewContext, select: miru.Button) -> None:
                class MyModal(miru.Modal, title="Template Creation"):
                    template_name = miru.TextInput(
                        label="Template Name",
                        placeholder="What's the name of the template?",
                        required=True,
                        max_length=40,
                        style=hikari.TextInputStyle.SHORT,
                    )

                    task_name = miru.TextInput(
                        label="Task Name",
                        placeholder="What's the name of the task?",
                        required=True,
                        max_length=botapp.d['max_name_length'],
                    )

                    task_desc = miru.TextInput(
                        label="Task Description",
                        placeholder="What's the description of the task?",
                        required=False,
                        max_length=botapp.d['max_desc_length'],
                        style=hikari.TextInputStyle.PARAGRAPH,
                    )

                    task_catagory = miru.TextInput(
                        label="Task Category",
                        placeholder="What category does this task belong to?",
                        required=False,
                        style=hikari.TextInputStyle.SHORT,
                    )

                    task_deadline_time = miru.TextInput(
                        label="Task Deadline Time",
                        placeholder="Strict Format \"DD/MM/YYYY HH:MM AM/PM\"",
                        required=False,
                    )

                    # The callback function is called after the user hits 'Submit'
                    async def callback(self, ctx: miru.ModalContext) -> None:
                        template_name = str(self.template_name.value).strip()
                        task_name = str(self.task_name.value).strip()
                        task_desc = str(self.task_desc.value).strip()
                        task_category = str(self.task_catagory.value).strip()
                        task_deadline_time = str(self.task_deadline_time.value).strip()

                        if template_name == "*":
                            await ctx.edit_response(
                                hikari.Embed(
                                    title="Template Creation Failed!",
                                    description="Template name cannot be \"*\" as that's reserved for the system!"
                                )
                            )
                        if task_name == "*":
                            await ctx.edit_response(
                                hikari.Embed(
                                    title="Template Creation Failed!",
                                    description="Task name cannot be \"*\" as that's reserved for the system!"
                                )
                            )

                        deadline_obj = None
                        if task_deadline_time != "":
                            try:
                                task_deadline_date = task_deadline_time.split(" ")[0]
                                task_deadline_hour = task_deadline_time.split(" ")[1]
                            except IndexError:
                                await ctx.edit_response(
                                    embed=hikari.Embed(
                                        title="Couldn't understand Deadline!",
                                        description="Please make sure you're using the correct format!",
                                        color=0xff0000,
                                    )
                                )
                                return

                            deadline_obj = parse_deadline(
                                deadline_date=task_deadline_date,
                                deadline_hmp=task_deadline_hour
                            )
                            if deadline_obj is str:  # This function returns a string detailing the error on fail.
                                await ctx.edit_response(
                                    embed=hikari.Embed(
                                        title="Couldn't understand Deadline!",
                                        description=deadline_obj,
                                        color=0xff0000,
                                    )
                                )
                                return

                        result = dataMan().create_task_template(
                            template_name=template_name,
                            task_name=task_name,
                            task_desc=task_desc,
                            task_category=task_category,
                            task_deadline=deadline_obj,
                            guild_id=ctx.guild_id,
                        )
                        success, template_id = result['success'], result['template_id']

                        if success:
                            await ctx.edit_response(
                                hikari.Embed(
                                    title="Template Created!",
                                    description=f"Unique Template ID: {template_id}"
                                )
                            )
                        else:
                            await ctx.edit_response(
                                hikari.Embed(
                                    title="Template Creation Failed!",
                                    description=f"Something went wrong! Please try again in a moment."
                                )
                            )
                            return

                modal = MyModal()
                builder = modal.build_response(miru_client)
                await builder.create_modal_response(ctx.interaction)
                miru_client.start_modal(modal)

        return Menu_Init()