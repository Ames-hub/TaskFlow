from library.live_task_channel import livetasks
from library.perms import perms
from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='task_id',
    description='What is the name or ID for the task?',
    required=True,
    default=None
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='unassign', description="Remove from a task who's been assigned", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def assign_cmd(ctx: lightbulb.SlashContext, task_id:int):
    dm = dataMan()

    allowed = await perms.is_privileged(
        guild_id=ctx.guild_id,
        user_id=ctx.author.id,
        permission=dm.get_guild_configperm(ctx.guild_id)
    )
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, missing_perm="Manage Server")
        return

    # Could use the check task exists, except that requires a task ID (number) this is a number OR name.
    tasks_list = dm.get_todo_items(
        identifier=task_id,
        filter_for="*"
    )

    if len(tasks_list) > 1:
        await ctx.respond(
            hikari.Embed(
                title="Too many Tasks!",
                description="There were too many tasks for that filter query for this command."
            )
        )
        return
    elif len(tasks_list) == 0:
        await ctx.respond(
            hikari.Embed(
                title="No tasks found",
                description="Please change the search query"
            )
        )
        return

    success = dm.clear_task_incharge(task_id=task_id)
    if success:
        await ctx.respond(
            hikari.Embed(
                title="Done",
                description=f"Task no longer has an incharge."
            )
        )
        await livetasks.update_for_guild(ctx.guild_id)
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Something went wrong clearing the task in-charge! :("
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
