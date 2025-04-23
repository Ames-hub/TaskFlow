from cogs.other.views.report_response_select_view import main_view as report_result_viewmenu
from library.botapp import miru_client
from library.storage import dataMan
import dotenv
import hikari
import miru
import os

dotenv.load_dotenv('.env')

class main_view:
    def __init__(self):
        pass

    # noinspection PyMethodMayBeStatic
    def gen_embed(self):
        maintainer_id = os.getenv('PRIMARY_MAINTAINER_ID')
        return (
            hikari.Embed(
                title="Bug Management",
                description=f"Welcome, <@{maintainer_id}>!"
            )
        )

    def init_view(self):
        bug_reports = dataMan().list_bug_reports(unresolved_only=True)
        bug_report_options = []
        for bug_report in bug_reports:
            bug_report_options.append(
                miru.SelectOption(
                    label=f"Ticket {bug_report['ticket_id']}",
                    # Saves some resources, even if a little inelegant.
                    value=f"{bug_report['ticket_id']} | {bug_report['reporter_id']}"
                )
            )

        if len(bug_report_options) == 0:
            bug_report_options.append(
                miru.SelectOption(
                    label="No Bug Reports",
                    value="None | -1"
                )
            )

        class Menu_Init(miru.View):
            # noinspection PyUnusedLocal
            @miru.button(label="Exit", style=hikari.ButtonStyle.DANGER)
            async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
                await ctx.edit_response(
                    hikari.Embed(
                        title="Exitting menu.",
                    ),
                    components=[]
                )
                self.stop()  # Called to stop the view

            # noinspection PyUnusedLocal
            @miru.text_select(
                options=bug_report_options
            )
            async def respond_btn(self, ctx: miru.ViewContext, select: miru.text_select) -> None:
                ticket_id, reporter_id = str(select.values[0]).split(" | ")

                if ticket_id == "None":
                    await ctx.edit_response(
                        hikari.Embed(
                            title="No Bug Reports",
                            description="There are no bug reports to view!"
                        ),
                        components=[]
                    )
                    return
                else:
                    ticket_id = int(ticket_id)
                    reporter_id = int(reporter_id)

                # Allow this one to stop to allow the next view
                self.stop()

                view = report_result_viewmenu(reporter_id=reporter_id, ticket_id=ticket_id)
                viewmenu = view.init_view()

                # Get the bug by ticket
                ticket = dataMan().list_bug_reports(ticket_id=ticket_id)[0]

                stated_bug = ticket['stated_bug']
                stated_reproduction = ticket['stated_reproduction']
                stated_additional = ticket['additional_info']

                embed = (
                    hikari.Embed(
                        title="Results are in?",
                        description=f"Ticket ID: {ticket_id}\nReporter ID: {reporter_id}\n\n"
                                    "How'd it go?",
                    )
                    .add_field(
                        name="Reported Bug",
                        value=stated_bug,
                    )
                    .add_field(
                        name="How to reproduce",
                        value=stated_reproduction
                    )
                )

                if stated_additional is not None:
                    embed.add_field(
                        name="Additional Info",
                        value=stated_additional
                    )

                await ctx.edit_response(
                    embed,
                    components=viewmenu.build()
                )

                miru_client.start_view(viewmenu)
                await viewmenu.wait()

        return Menu_Init()