from library.parsing import parse_livelist_format
from library.botapp import miru_client
from library.storage import dataMan
import lightbulb
import datetime
import hikari
import miru

plugin = lightbulb.Plugin(__name__)
style_choices = ['classic', 'minimal', 'pinned', 'compact', 'pinned-minimal']

class view:
    class style_select_view(miru.View):
        @miru.text_select(
            placeholder="Select a style",
            options=[
                miru.SelectOption(label=style.capitalize(), value=style.lower()) for style in style_choices
            ],
            custom_id='style_select',
        )
        async def get_text(self, viewctx: miru.ViewContext, select: miru.text_select) -> None:
            dm = dataMan()
            success:bool = dm.set_livechannel_style(str(select.values[0]), int(viewctx.guild_id))

            if success:
                await viewctx.edit_response(
                    hikari.Embed(
                        title="Style selected",
                        description=f"Style set to {select.values[0]}.",
                        color=0x2b2d31
                    ),
                    components=[],  # Remove the view
                    flags=hikari.MessageFlag.EPHEMERAL
                )
            else:
                await viewctx.edit_response(
                    hikari.Embed(
                        title="Error",
                        description="An error occurred while setting the style :(",
                        color=0xFF0000
                    ),
                    components=[],
                    flags=hikari.MessageFlag.EPHEMERAL
                )

        learn_more = miru.LinkButton(
            url="https://gist.github.com/Ames-hub/d66e88c4780234682efc20eea62e94f0", label="Custom Styling Help"
        )

        # noinspection PyUnusedLocal
        @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER)
        async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
            await ctx.edit_response(
                embed=hikari.Embed(
                    title="Done",
                    description="Live Task Styling Exited."
                ),
                components=[]
            )
            self.stop()  # Called to stop the view

        # noinspection PyUnusedLocal
        @miru.button(label="Set Custom Style", emoji="🎨")
        async def custom_style(self, ctx: miru.ViewContext, button: miru.Button):
            class MyModal(miru.Modal, title="Format the style\n"):

                live_format = miru.TextInput(
                    label="format",
                    placeholder=(
                        "Please enter the message format to follow."
                    ),
                    required=True,
                    style=hikari.TextInputStyle.PARAGRAPH
                )

                # The callback function is called after the user hits 'Submit'
                async def callback(self, ctx: miru.ModalContext) -> None:
                    live_format = self.live_format.value.lower()

                    success = dataMan().save_livelist_format(ctx.guild_id, live_format)
                    if success:
                        await ctx.edit_response(
                            hikari.Embed(
                                description="Your live list format is set!"
                            )
                            .add_field(
                                name="Original",
                                value=live_format
                            )
                            .add_field(
                                name="Example Result",
                                value=parse_livelist_format(
                                    live_format,
                                    task_item={ # ['id', 'name', 'description', 'completed', 'added_by', 'completed_on']
                                        'id': 1,
                                        'name': "Test the Style",
                                        'description': "Does this desc work? Lets see!",
                                        'completed': True,
                                        'added_by': 913574723475083274,
                                        'completed_on': datetime.datetime.now(),
                                    },
                                    contrib_count=32
                                )
                            )
                        )
                    else:
                        await ctx.edit_response(
                            hikari.Embed(
                                title="Uh oh!",
                                description="Your live list format couldn't be saved!"
                            )
                        )

            modal = MyModal()
            builder = modal.build_response(miru_client)
            await builder.create_modal_response(ctx.interaction)
            miru_client.start_modal(modal)
