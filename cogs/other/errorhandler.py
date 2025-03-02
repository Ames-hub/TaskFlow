import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(lightbulb.CommandErrorEvent)
async def on_error(event: lightbulb.CommandErrorEvent) -> None:
    if isinstance(event.exception, lightbulb.MissingRequiredPermission):
        await event.context.respond("You don't have the required permissions to run this command.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.MissingRequiredRole):
        await event.context.respond("You don't have the required role to run this command.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.BotMissingRequiredPermission):
        await event.context.respond("I don't have the required permissions to run this command!", flags=hikari.MessageFlag.EPHEMERAL)   
    elif isinstance(event.exception, lightbulb.errors.OnlyInDM):
        await event.context.respond("This command can only be run in DMs.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.OnlyInGuild):
        await event.context.respond("This command can only be run in a guild.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.NSFWChannelOnly):
        await event.context.respond("This command can only be run in a NSFW channel.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.NotOwner):
        await event.context.respond("You are not the owner of this bot.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.CommandIsOnCooldown):
        await event.context.respond(f"You have {event.exception.retry_after:.2f} seconds left before you can run this command again.")
    elif isinstance(event.exception, lightbulb.errors.BotOnly):
        await event.context.respond("This command can only be run by bots.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.NotEnoughArguments):
        await event.context.respond("We're missing some needed information to run this command!", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.InvalidArgument):
        await event.context.respond("Invalid information to run this command!", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.MissingRequiredAttachmentArgument):
        await event.context.respond("You need to attach a file to run this command.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, lightbulb.errors.CommandNotFound):
        pass # Ignore this error, since it is not a problem.
    elif isinstance(event.exception, hikari.errors.NotFoundError):
        await event.context.respond("Something went wrong with the interaction.\nPlease run the command again.", flags=hikari.MessageFlag.EPHEMERAL)
    elif isinstance(event.exception, TimeoutError):
        await event.context.respond("Command timed out.", flags=hikari.MessageFlag.EPHEMERAL)
    else:
        await event.context.respond("An error occurred while running this command :(\nPlease try again later once we solve the problem.", flags=hikari.MessageFlag.EPHEMERAL)
        raise event.exception
    print(f"An error occurred while running a command: {event.exception}")
    
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(lightbulb.Plugin(__name__))
