from cogs.other.views.bugreports.bug_manage_view import main_view as bug_manage_view
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
                title="Feature Request",
                description="Do you have an idea to improve the bot? Let us know!\n"
            )
            .add_field(
                name="How to send a request",
                value="You need to Click the button below, 'open request screen'.\n\n"
            )
            .add_field(
                name="Guidelines",
                value=(
                    "**Do**: Describe your idea in specifics, like 'A view command with options' isn't too helpful for me, as I still don't know what you want. "
                    "But 'A view command with options A, B and C that do X, Y and Z' is much more helpful.\n\n"
                    
                    "**Do**: Understand that I will not implement every idea, and that if I don't implement your idea, it doesn't mean it's a bad one. "
                    "Sometimes, it just isn't possible, or discord has limits, or its any other of the thousand possible reasons.\n\n"
                )
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
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            # noinspection PyUnusedLocal
            @miru.button(label="Show Request Screen!", emoji="🪲")
            async def report_btn(self, ctx: miru.ViewContext, select: miru.Button) -> None:
                class MyModal(miru.Modal, title="Feature Request Screen"):
                    feature_request = miru.TextInput(
                        label="Your Idea",
                        placeholder="What's your idea?",
                        required=True,
                        max_length=2000,
                        style=hikari.TextInputStyle.PARAGRAPH,
                    )

                    pos_use = miru.TextInput(
                        label="What's the use case?",
                        placeholder="How could this be used by users of the bot?",
                        required=True,
                        max_length=1000,
                        style=hikari.TextInputStyle.PARAGRAPH,
                    )

                    # The callback function is called after the user hits 'Submit'
                    async def callback(self, ctx: miru.ModalContext) -> None:
                        maintainer_id = int(os.getenv('PRIMARY_MAINTAINER_ID'))

                        embed = (
                            hikari.Embed(
                                title="New Suggestion!",
                                description=f"User {ctx.author.username} Has suggested a new feature!",
                            )
                            .add_field(
                                name="Idea",
                                value=self.feature_request.value
                            )
                            .add_field(
                                name="How its used",
                                value=self.pos_use.value
                            )
                        )

                        dmc = await ctx.client.rest.create_dm_channel(maintainer_id)
                        await dmc.send(embed)

                        await ctx.edit_response(
                            hikari.Embed(
                                title="Request Sent!",
                                description="Idea's help anything grow, so thank you!",
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