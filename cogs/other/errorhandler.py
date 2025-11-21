from library.storage import dataMan, save_traceback
from library.botapp import botapp
import lightbulb
import traceback
import datetime
import logging
import hikari
import io
import os

plugin = lightbulb.Plugin(__name__)

async def report_bug(event):
    maintainer_id = int(botapp.d['PRIMARY_MAINTAINER_ID'])
    dmc = await botapp.rest.create_dm_channel(maintainer_id)  # The bot maintainer's ID.

    tb = traceback.format_exception(type(event.exception), event.exception, event.exception.__traceback__)

    # Forms an attachment with the traceback using bytesIO library
    data = io.BytesIO("".join(tb).encode("utf-8"))
    attachment = hikari.Bytes(
        data,
        "error_traceback.txt",
    )

    in_guild = event.context.guild_id is not None

    # For some reason, event.context.command.name is only returning the group for subcommands. So we must
    # Do it in this more complicated way by examining the exception and looking for the command.
    command_name = "N/A"
    command_desc = "N/A"
    is_command = False
    path_filter = os.getcwd()

    for tb_line in tb:
        if f"File \"{path_filter}" in tb_line:
            # Finds the text inbetween the quotes
            directory = tb_line[tb_line.find("\"") + 1:tb_line.rfind("\"")]
            if "cogs" in directory:
                is_command = True
                try:
                    with open(directory, 'r') as f:
                        lines = f.readlines()
                        for cmdfile_line in lines:
                            # EG: @lightbulb.command(name='Test', description='Test Cmd')
                            if "@lightbulb.command(" in cmdfile_line:
                                # Handles both upper and lower case name and description
                                if "name='" in cmdfile_line:
                                    command_name = cmdfile_line[cmdfile_line.find("name='") + 6:cmdfile_line.find("', description=")]
                                    name_end = cmdfile_line.find("', description=")
                                else:
                                    command_name = cmdfile_line[cmdfile_line.find("name=\"") + 6:cmdfile_line.find("\", description=")]
                                    name_end = cmdfile_line.find("\", description=")

                                if "description='" in cmdfile_line:
                                    # For edge cases like
                                    # @lightbulb.command(name='make_task', description="Create a task from a template", pass_options=True)
                                    # Handle if there's another argument
                                    if "'," in cmdfile_line[:name_end]:
                                        command_desc = cmdfile_line[cmdfile_line.find("description='") + 13:cmdfile_line.find("',")]
                                    else:
                                        command_desc = cmdfile_line[cmdfile_line.find("description='") + 13:cmdfile_line.find("')")]
                                else:
                                    if "\"," in cmdfile_line[:name_end]:
                                        command_desc = cmdfile_line[cmdfile_line.find("description=\"") + 13:cmdfile_line.find("\",")]
                                    else:
                                        command_desc = cmdfile_line[cmdfile_line.find("description=\"") + 13:cmdfile_line.find("\")")]

                                err_directory = directory
                                break
                except FileNotFoundError:
                    err_directory = "File not found"
                    break

    option_list = []
    for item in event.context.options.items():
        opt_name = item[0]
        opt_value = item[1]

        option_list.append(f"{opt_name} = {opt_value}")

    pos_options_count = len(event.context.command.options)
    options_count = len(option_list)

    if len(option_list) == 0:
        option_list.append("No options selected")

    # Log a bug report without sending the DM
    ticket_id = dataMan().create_bug_report_ticket(
        reporter_id=event.context.author.id,
        stated_bug=f"I encountered an error in the {command_name.replace("_", " ")} command!",
        stated_reproduction=f"Run the command with options {event.context.options.items()}",
        problem_section=f"'{command_name}' Bot command",
        expected_result="N/A: Automated Report.",
        additional_info="This bug report was sent automatically when you tried to use the bot, but encountered an error!",
        return_ticket=True
    )

    report = dataMan().list_bug_reports(ticket_id=ticket_id)[0]

    await dmc.send(
        hikari.Embed(
            title=f"Error!  :(",
            description=f"Command: {command_name}\n"
                        f"Description: {command_desc}\n"
                        f"Is Command: {is_command}\n"
                        f"File Exception Path: {err_directory}\n",
            timestamp=datetime.datetime.now().astimezone(),
            color=hikari.Color(0xff0000)
        )
        .set_author(
            name=event.context.author.username,
            icon=event.context.author.avatar_url,
        )
        .add_field(
            name="CONTEXT",
            value=f"The user encountered the error \n\"{event.exception}\" at the posted timestamp. A full traceback is attached.\n\n"
                  f"Invoker: {event.context.author.id} ({event.context.author.username})\n"
                  f"In a Guild?: {in_guild}\n"
                  f"Guild ID: {event.context.guild_id}\n"
                  f"Is this a DM?: {not in_guild}\n"
                  f"Is this bot an official instance?: {botapp.get_me().id in [1387493386575020164, 1090899298650169385]}\n"
        )
        .add_field(
            name="OPTIONS",
            value=f"Command has options?: {'True' if pos_options_count > 0 else 'False'}\n"
                  f"User used {options_count}/{pos_options_count} possible options.\n"
                  f"Options used are as listed below.\n"
                  f"{"\n".join(option_list)}",
        )
        .add_field(name="Bug", value=report['stated_bug'])
        .add_field(name="Problem Section", value=report['problem_section'])
        .add_field(name="Expected result", value=report['expected_result'])
        .add_field(name="How to reproduce", value=report['stated_reproduction']),
        attachment=attachment
    )

    return ticket_id

# For some reason, using plugin.listener doesn't work
@botapp.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if not isinstance(event.exception, lightbulb.errors.CommandIsOnCooldown):
        logging.info("Error handler firing for unhandled exception.")

    if isinstance(event.exception, lightbulb.MissingRequiredPermission):
        embed = (
            hikari.Embed(
                title="Insufficient permissions",
                description="You do not have permission to use this command!",
            )
        )
        await event.context.respond(
            embed,
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    elif isinstance(event.exception, lightbulb.MissingRequiredRole):
        await event.context.respond("You don't have the required role to run this command.", flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif isinstance(event.exception, lightbulb.BotMissingRequiredPermission):
        await event.context.respond("I don't have the required permissions to run this command!", flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif isinstance(event.exception, lightbulb.errors.OnlyInDM):
        await event.context.respond("This command can only be run in DMs.", flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif isinstance(event.exception, lightbulb.errors.OnlyInGuild):
        await event.context.respond("This command can only be run in a guild.", flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif isinstance(event.exception, lightbulb.errors.NotOwner):
        await event.context.respond("You are not the owner of this bot.", flags=hikari.MessageFlag.EPHEMERAL)
        return
    elif isinstance(event.exception, lightbulb.errors.CommandIsOnCooldown):
        wait_time = int(event.exception.retry_after)  # In seconds
        if wait_time <= 120:  # Under 2 minutes
            time_unit = "second(s)"
            # No change to wait_time (remains in seconds).
        elif wait_time <= 3599:  # Under an hour
            time_unit = "minute(s)"
            wait_time = wait_time // 60  # Convert seconds to minutes.
        elif wait_time <= 86399:  # Less than a day (under 24 hours)
            time_unit = "hour(s)"
            wait_time = wait_time // 3600  # Convert seconds to hours.
        else:  # Greater than or equal to 1 day
            time_unit = "day(s)"
            wait_time = wait_time // 86400  # Convert seconds to days.

        embed = (
            hikari.Embed(
                title="Command is on cooldown",
                description=f"You have {wait_time} {time_unit} left before you can run this command again."
            )
        )
        await event.context.respond(embed)
        return
    elif isinstance(event.exception, hikari.errors.NotFoundError):
        logging.warning("An unintended keep-alive timeout for a command occured!")
        return
    else:
        print(f"An error occurred while running a command: {event.exception}")
        logging.error(f"A ({type(event.exception)}) error occurred while {event.context.author.id} was running a command: {event.exception}", exc_info=event.exception)

        await event.context.respond(
            embed=hikari.Embed(
                title="Error!",
                description="An error occurred while running this command.",
                colour=0xff0000,
            )
            .add_field(
                name="Auto-Reporting",
                value="A Bug report has been automatically filed and sent to the maintainer.\n\n"
                "To learn about the latest bug patches and features, use `/news`!",
            )
        )

        try:
            bug_id = await report_bug(event)
            save_traceback(bug_id, event.exception)
        except Exception as err:
            logging.error(f"Failed to alert maintainer and report bug: {err}", exc_info=err)

        raise event.exception
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))
