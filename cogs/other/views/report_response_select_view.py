from library.botapp import botapp, miru_client
from library.storage import dataMan
from datetime import datetime
import dotenv
import hikari
import miru


dotenv.load_dotenv('.env')

class main_view:
    def __init__(self, reporter_id, ticket_id):
        self.reporter_id = reporter_id
        self.ticket_id = ticket_id

    def init_view(self):
        reporter_id = self.reporter_id
        ticket_id = self.ticket_id
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
                options=[
                    miru.SelectOption(
                        label="Resolved",
                        value="RESOLVED"
                    ),
                    miru.SelectOption(
                        label="Unable to reproduce",
                        value="NO-REPRODUCE"
                    ),
                    miru.SelectOption(
                        label="Intended functionality",
                        value="INTENDED"
                    ),
                    miru.SelectOption(
                        label="Unclear Bug Report",
                        value="UNCLEAR"
                    ),
                    miru.SelectOption(
                        label="To the Backburner",
                        value="BACKBURNER"
                    ),
                    miru.SelectOption(
                        label="No Fix will be implemented",
                        value="WONT-FIX"
                    ),
                    miru.SelectOption(
                        label="I want to respond personally",
                        value="CUSTOM"
                    ),
                    miru.SelectOption(
                        label="Hide Bug Report",
                        value="HIDE"
                    ),
                    miru.SelectOption(
                        label="Report Received",
                        value="RECEIVED"
                    )
                ]
            )
            async def respond_btn(self, ctx: miru.ViewContext, select: miru.text_select) -> None:
                report_result = str(select.values[0])
                custom_content = None
                timeout_mins = 3

                mark_resolved = True

                # TODO: Have this show their full bug report as well as the result so they know what happened if they forgot.
                if report_result == "RESOLVED":
                    report_result = "Thank you for reporting the bug! It has been resolved and the fix will be rolled out as soon as possible :)"
                elif report_result == "NO-REPRODUCE":
                    mark_resolved = False
                    report_result = ("Thank you for reporting the bug!\n"
                                     "Unfortunately, we didn't have enough information to recreate the bug, which is a crucial step in fixing it.\n\n"
                                     "If you can provide more information, please report the bug once more with that extra info. Thanks!")
                elif report_result == "INTENDED":
                    report_result = "Thank you, however what was reported was not a bug, but rather an intended feature, so nothing has been done.\n"
                elif report_result == "UNCLEAR":
                    mark_resolved = False
                    report_result = "The bug report was not clear enough to be quite understood, so nothing was able to be done."
                elif report_result == "BACKBURNER":
                    mark_resolved = False
                    report_result = ("Thank you! The bug has been noted and will be worked on. However due to its nature or the current situation;\n\n"
                                     "It has been placed on the backburner and will be worked on when possible.\n\n"
                                     "Please note: This does not mean we're ignoring it, it just means that we're not working on it right now.")
                elif report_result == "WONT-FIX":
                    report_result = ("Thank you for reporting the bug!\n"
                                     "We've decided to not fix this bug and leave it as-is or improve it as a feature.")
                elif report_result == "HIDE":
                    dataMan().mark_bugreport_resolved(ticket_id)

                    self.stop()
                    from cogs.other.views.bug_manage_view import main_view as bug_manage_view

                    view = bug_manage_view()
                    viewmenu = view.init_view()


                    await ctx.edit_response(
                        view.gen_embed().add_field(
                            name="Bug Report Hidden.",
                            value="The user has not been informed of anything."
                        ),
                        components=viewmenu.build()
                    )

                    return
                elif report_result == "CUSTOM":
                    await ctx.edit_response(
                        hikari.Embed(
                            title="Custom response",
                            description="We've sent you a DM. Respond with ONLY how you'd like the bot to respond."
                        )
                    )
                elif report_result == "RECEIVED":
                    mark_resolved = False
                    report_result = ("Thank you for reporting the bug!\n"
                                     "Your report has been received and read by the maintainers, and is being worked on."
                                     "You can usually expect a fix within 1 hour to 48 hours.")

                embed_cannot_send = hikari.Embed(
                    title="Couldn't send DM to reporter!",
                    description="This is likely due to the bot not having access to the user's DM channel.\n"
                                "Please try again later."
                )

                try:
                    if custom_content is not None:
                        report_result = custom_content

                    bug_ticket = dataMan().list_bug_reports(ticket_id=ticket_id)[0]

                    try:
                        dmc = await botapp.rest.create_dm_channel(reporter_id)
                    except (hikari.ForbiddenError, hikari.NotFoundError, hikari.BadRequestError):
                        await ctx.edit_response(
                            embed_cannot_send,
                            components=[]
                        )
                        return

                    await dmc.send(
                        hikari.Embed(
                            title="Bug report result",
                            description=f"This is regarding a bug report you filed a while ago with Ticket ID {ticket_id}.\n\n",
                            color=0x00ff00,
                            timestamp=datetime.now().astimezone()
                        )
                        .add_field(
                            name=f"Bug Report {ticket_id}",
                            value=f"Status: {"RESOLVED" if mark_resolved else "Still unresolved."}\n" 
                                  f"Stated Bug: {bug_ticket['stated_bug']}"
                        )
                        .add_field(name="Message", value=report_result)
                    )
                    # Mark the ticket as resolved
                    if mark_resolved:
                        dataMan().mark_bugreport_resolved(ticket_id)

                    self.stop()
                    from cogs.other.views.bug_manage_view import main_view as bug_manage_view

                    view = bug_manage_view()
                    viewmenu = view.init_view()

                    await ctx.edit_response(
                        view.gen_embed().add_field(
                            name="Bug report result sent!",
                            value="The user has been informed of the result of their bug report."
                        ),
                        components=viewmenu.build()
                    )

                    miru_client.start_view(viewmenu)
                    await viewmenu.wait()
                except (hikari.ForbiddenError, hikari.NotFoundError):
                    await ctx.edit_response(
                        embed_cannot_send,
                        components=[]
                    )
                    return

        return Menu_Init()