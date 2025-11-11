from library.storage import dataMan
from library.botapp import botapp
from library.perms import perms
import lightbulb
import traceback
import datetime
import logging
import dotenv
import hikari
import io
import os

plugin = lightbulb.Plugin(__name__)

async def alert_maintainer(event):
    dotenv.load_dotenv('.env')
    maintainer_id = int(os.environ.get("PRIMARY_MAINTAINER_ID"))
    dmc = await event.bot.rest.create_dm_channel(maintainer_id)  # The bot maintainer's ID.

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

    pos_options_count = len(event.context.command.options.keys())
    options_count = len(option_list)

    if len(option_list) == 0:
        option_list.append("No options selected")

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
                  # Modify those numbers without also setting the primary_maintainer_id in .env to somebody else, and I will cry :3
                  f"Is this bot an official instance?: {botapp.get_me().id in [1262021444615933962, 1090899298650169385]}\n"
        )
        .add_field(
            name="OPTIONS",
            value=f"Command has options?: {'True' if pos_options_count > 0 else 'False'}\n"
                  f"User used {options_count}/{pos_options_count} possible options.\n"
                  f"Options used are as listed below.\n"
                  f"{"\n".join(option_list)}",
        ),
        attachment=attachment
    )

    # Log a bug report without sending the DM
    dataMan().create_bugreport_ticket(
        reporter_id=event.context.author.id,
        stated_bug=f"I encountered an error in the {command_name.replace("_", " ")} command!",
        stated_reproduction=f"Run the command with options {event.context.options.items()}",
        additional_info="This bug report was sent automatically!"
    )

# For some reason, using plugin.listener doesn't work
@botapp.listen(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if not isinstance(event.exception, lightbulb.errors.CommandIsOnCooldown):
        logging.info("Error handler firing for unhandled exception.")

    if isinstance(event.exception, lightbulb.MissingRequiredPermission):
        await event.context.respond(
            perms.embeds.insufficient_perms(event.context),
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
        await event.context.respond(f"You have {event.exception.retry_after:.2f} seconds left before you can run this command again.")
        return
    elif isinstance(event.exception, hikari.errors.NotFoundError):
        logging.warning("An unintended keep-alive timeout for a command occured!")
        return
    elif isinstance(event.exception, hikari.errors.ForbiddenError):
        await event.context.respond(
            hikari.Embed(
                title="Uh oh!",
                description="I don't have permission to do that!\n"
                            "Please check my permissions and try again."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )

    # THE BELOW ARE UNHANDLED, UNEXPECTED ERRORS.
    elif isinstance(event.exception, Exception):
        if event.context:
            await event.context.respond(
                hikari.Embed(
                    title="Uh oh!",
                    description="Sorry, it seems an unknown problem occured!\n"
                                "Don't worry, the project maintainers have been alerted."
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )

        logging.info("Error!", exc_info=event.exception)
        await alert_maintainer(event)
    else:
        await event.context.respond("An error occurred while running this command :(\n"
                                    "Don't worry, the project maintainers have been alerted.", flags=hikari.MessageFlag.EPHEMERAL)
        await alert_maintainer(event)

    print(f"An error occurred while running a command: {event.exception}")
    logging.error(f"An error occurred while running a command: {event.exception}", exc_info=event.exception)
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))
