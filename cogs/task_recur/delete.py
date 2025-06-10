from library.storage import dataMan, error
from cogs.task_recur.group import group
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='identifier',
    description="What's the Recur ID of the recurring task?",
    required=True,
    type=hikari.OptionType.INTEGER
)
@lightbulb.command(name='remove', description='Remove a recurring task by an assosciated task/recur ID', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, identifier: int):
    dm = dataMan()

    # Test if in guild
    try:
        owning_guild_id = dm.get_recur_guild_id(identifier)
    except error.CannotFind:
        await ctx.respond(
            hikari.Embed(
                title="Not Found",
                description="Couldn't find the recurring item with that recur ID!",
            )
        )
        return

    if owning_guild_id != ctx.guild_id:
        await ctx.respond(
            hikari.Embed(
                title="Unauthorized",
                description="You are not authorized to delete this task.",
            )
        )
        return

    success = dm.delete_recurring_task(identifier)

    if success:
        embed = (
            hikari.Embed(
                title='Recurring Task deleted',
                description=f"Recurring Task's assosciated Recur ID and assosciated tasks deleted successfully."
            )
        )
    else:
        embed = (
            hikari.Embed(
                title='Uh oh!',
                description=f"Couldn't delete this recurring task.\nPlease submit a bug report so we know what went wrong!"
            )
        )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
