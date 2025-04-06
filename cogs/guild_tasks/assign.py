from library.live_task_channel import livetasks
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
@lightbulb.option(
    name='user',
    description='Which user do you want to assign?',
    required=False,
    default=None
)
@lightbulb.command(name='assign', description="Assign a member to a task as an in-charge", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def assign_cmd(ctx: lightbulb.SlashContext, task_id:int, user:hikari.User):
    dm = dataMan()

    tasks_list = dm.get_todo_items(
        identifier=task_id,
        filter_for="*"
    )

    if user is None:
        user = ctx.author

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

    success = dm.assign_user_to_task(user_id=user.id, task_id=task_id, guild_id=ctx.guild_id)
    if success:
        await ctx.respond(
            hikari.Embed(
                title="Assigned",
                description=f"<@{user.id}> is now the designated in-charge for the task."
            )
        )
        await livetasks.update(ctx.guild_id)
    elif success == -1:
        await ctx.respond(
            hikari.Embed(
                title="Insufficient Permissions",
                description=f"That's a task for another server."
            )
        )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Something went wrong assigning the task! :("
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
