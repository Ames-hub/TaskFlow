from library.live_task_channel import livetasks
from cogs.guild_tasks.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='task_id',
    description="What's the ID of the task to delete?",
    required=True,
    type=hikari.OptionType.INTEGER,
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='delete', description='Delete a task from the list.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def delete_task_cmd(ctx: lightbulb.SlashContext, task_id:int):
    dm = dataMan()

    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    # Prevents users from deleting another guilds tasks
    if not dm.crossref_task(task_id) == int(ctx.guild_id):
        await ctx.respond(
            hikari.Embed(
                title="Task Forbidden",
                description="This task is not from your server."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    success = dm.delete_task_from_list(task_id)
    if success == -1:
        await ctx.respond(
            hikari.Embed(
                title="Task Not Found",
                description="Could not delete that task as it does not exist."
            )
        )
    elif success is True:
        await ctx.respond(
            hikari.Embed(
                title="Success",
                description="Task deleted",
            )
        )
        await livetasks.update_for_guild(int(ctx.guild_id))
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Something went wrong!"
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
