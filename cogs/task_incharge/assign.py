from library.live_task_channel import livetasks
from cogs.task_incharge.group import group
from library.storage import dataMan
from library.perms import perms
from library import tferror
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='task_id',
    description='What is the name or ID for the task?',
    type=hikari.OptionType.INTEGER,
    required=True,
    default=None
)
@lightbulb.option(
    name='user',
    description='Which user do you want to assign?',
    type=hikari.OptionType.USER,
    required=False,
    default=None
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='assign', description="Assign a member to a task as an in-charge", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def assign_cmd(ctx: lightbulb.SlashContext, task_id:int, user:hikari.User):
    dm = dataMan()
    task_incharge = user  # Rename for backend clarity
    del user

    # TODO: make needing a permission to assign or unassign a task to someone toggleable.
    allowed = await perms.is_privileged(
        guild_id=ctx.guild_id,
        user_id=ctx.author.id,
        permission=dm.get_guild_configperm(ctx.guild_id)
    )
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, missing_perm="Manage Server")
        return

    tasks_list = dm.get_todo_items(
        identifier=task_id,
        filter_for="*"
    )

    if task_incharge is None:
        task_incharge = ctx.author

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

    incharge_id = int(task_incharge.id)

    success = dataMan().assign_user_to_task(
        user_id=incharge_id,
        task_id=task_id,
        guild_id=int(ctx.guild_id)
    )
    dataMan().mark_user_as_contributing(
        user_id=incharge_id,
        task_id=task_id,
        guild_id=int(ctx.guild_id)
    )

    if success:
        await ctx.respond(
            hikari.Embed(
                title="Assigned",
                description=f"<@{task_incharge.id}> is now the designated in-charge for the task."
            )
        )
        
        try:
            await livetasks.update_for_guild(ctx.guild_id)
        except tferror.livelist.no_channel:
            pass  # We don't care if we can't update the live list here.

        guild = await ctx.bot.rest.fetch_guild(ctx.guild_id)
        task_name = tasks_list[task_id]['name']
        embed = (
            hikari.Embed(
                title="Role assignment!",
                description=f"You have been assigned as the in-charge for the task '{task_name}' (Task ID {task_id}) by {ctx.author.mention}."
                f"\n\nThis happened in the server '{guild.name}'.",
                color=0x00FF00
            )
            .add_field(
                name="What's this mean?",
                value="Being in-charge means you are primarily responsible for this task. "
                "You will be able to control who's helping, and have access to coordination tools."
            )
        )
        await task_incharge.send(embed)
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
