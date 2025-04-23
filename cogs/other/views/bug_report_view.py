from cogs.other.views.bug_manage_view import main_view as bug_manage_view
from library.botapp import miru_client
from library.storage import dataMan
import dotenv
import hikari
import miru
import os

dotenv.load_dotenv('.env')

class main_view:
    def __init__(self, author_id):
        self.author_id = author_id

    # noinspection PyMethodMayBeStatic
    def gen_embed(self):
        return (
            hikari.Embed(
                title="Bug report",
                description="Thank you for reporting a bug!\n"
            )
            .add_field(
                name="How to report a bug",
                value="1. You need to Click the button below to open the reporting screen.\n\n"
                      "2. When you see the screen, fill out the fields to the best of your ability. Please be specific and detailed ^^\n\n"
                      "3. Once you're done, click the submit button!"
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

            # Simpler than figuring out 'add_item' since the documentation on it is not enough.
            if int(self.author_id) == int(os.getenv('PRIMARY_MAINTAINER_ID')):
                # noinspection PyUnusedLocal
                @miru.button(label="Manage", style=hikari.ButtonStyle.SECONDARY)
                async def bug_manage_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                    # Stop current view to start new one
                    self.stop()

                    view = bug_manage_view()
                    viewmenu = view.init_view()

                    await ctx.edit_response(
                        embed=view.gen_embed(),
                        components=viewmenu.build()  # Change to a completely different view.
                    )

                    miru_client.start_view(viewmenu)
                    await viewmenu.wait()

            # noinspection PyUnusedLocal
            @miru.button(label="Show Reporting Screen!", emoji="🪲")
            async def report_btn(self, ctx: miru.ViewContext, select: miru.Button) -> None:
                class MyModal(miru.Modal, title="Bug Report Screen"):
                    bug = miru.TextInput(
                        label="Bug",
                        placeholder="How would you describe the bug?",
                        required=True,
                        max_length=1000,
                        style=hikari.TextInputStyle.PARAGRAPH,
                    )

                    reproduce = miru.TextInput(
                        label="How do I reproduce it?",
                        placeholder="Write exactly what you did which made the bug happen please!",
                        required=True,
                        max_length=1000,
                        style=hikari.TextInputStyle.PARAGRAPH
                    )

                    additional = miru.TextInput(
                        label="Additional Info",
                        placeholder="Any additional info you'd like to add?",
                        required=False,
                        max_length=1000,
                        style=hikari.TextInputStyle.PARAGRAPH,
                    )

                    # The callback function is called after the user hits 'Submit'
                    async def callback(self, ctx: miru.ModalContext) -> None:
                        maintainer_id = int(os.getenv('PRIMARY_MAINTAINER_ID'))

                        additional = self.additional.value
                        if additional == "":
                            additional = None

                        # Remembers that THIS user reported a bug so we can tell them how it went
                        ticket_id = dataMan().create_bugreport_ticket(
                            reporter_id=ctx.author.id,
                            stated_bug=self.bug.value,
                            stated_reproduction=self.reproduce.value,
                            additional_info=additional,
                            return_ticket=True
                        )

                        embed = (
                            hikari.Embed(
                                title=f"Bug report ({ticket_id})",
                                description=f"We got a bug report from {ctx.author.username}! ({ctx.author.id})\n\n",
                            )
                            .add_field(name="Bug", value=self.bug.value)
                            .add_field(name="How to reproduce", value=self.reproduce.value)
                        )
                        if additional is not None:
                            embed.add_field(name="Additional Info", value=additional)

                        dmc = await ctx.client.rest.create_dm_channel(maintainer_id)
                        await dmc.send(embed)

                        await ctx.edit_response(
                            hikari.Embed(
                                title="Bug reported!",
                                description="Thank you for reporting the bug!\n"
                                            "The bug has been forwarded to the project maintainers and will be fixed as soon as possible.\n"
                                            f"Your ticket ID: {ticket_id}",
                                color=0x00ff00,
                            ),
                            components=[]
                        )

                modal = MyModal()
                builder = modal.build_response(miru_client)
                await builder.create_modal_response(ctx.interaction)
                miru_client.start_modal(modal)

        menu = Menu_Init()

        return menu