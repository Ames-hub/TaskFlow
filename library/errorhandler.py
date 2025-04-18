from library.perms import perms
import lightbulb
import traceback
import datetime
import logging
import dotenv
import hikari
import io
import os

dotenv.load_dotenv('.env')
plugin = lightbulb.Plugin(__name__)

@plugin.listener(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.MissingRequiredPermission):
        await event.context.respond(
            perms.embeds.insufficient_perms(event.context),
            flags=hikari.MessageFlag.EPHEMERAL
        )
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
    elif isinstance(event.exception, Exception):
        if event.context:
            await event.context.respond(
                hikari.Embed(
                    title="Uh oh!",
                    description="Sorry, it seems an unknown problem occured!"
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )
        logging.info("Error!", exc_info=event.exception)
    else:
        await event.context.respond("An error occurred while running this command :(\nPlease try again later once we solve the problem.", flags=hikari.MessageFlag.EPHEMERAL)

    maintainer_id = int(os.getenv("{PRIMARY_MAINTAINER_ID"))
    dmc = await event.bot.rest.create_dm_channel(maintainer_id)  # The bot maintainer's ID.

    # Forms an attachment with the traceback using bytesIO library
    data = io.BytesIO(traceback.format_exc().encode("utf-8"))
    attachment = hikari.Bytes(
        data,
        "error_traceback.txt",
    )

    await dmc.send(
        hikari.Embed(
            title=f"Error in guild ID {event.context.guild_id} :(",
            description=f"Command: {event.context.command.name}\n",
            timestamp=datetime.datetime.now(),
        )
        .set_author(
            name=event.context.author.username,
            icon=event.context.author.avatar_url,
        )
        .add_field(
            name="CONTEXT",
            value=f"The user encountered the error \"{event.exception}\" at the posted timestamp. A full traceback is attached."
        ),
        attachment=attachment
    )
    print(f"An error occurred while running a command: {event.exception}")
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))
