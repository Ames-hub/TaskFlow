from cogs.task_incharge.group import group
from library.storage import dataMan
from library import shared
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='drafted_user',
    description="Who's being told to help?",
    type=hikari.OptionType.USER,
    required=True,
    default=None
)
@lightbulb.option(
    name='task_id',
    description='Enter the task ID to announce for',
    type=hikari.OptionType.INTEGER,
    required=False,
    default=None
)
@lightbulb.command(name='draft', description="Assign a member to help with a task.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext, drafted_user:hikari.Member, task_id):
    task_incharge = dataMan().get_task_incharge(task_id)
    if not task_incharge:
        embed = shared.get_no_incharge_embed()
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    if task_incharge != ctx.author.id:
        embed = shared.get_not_incharge_embed()
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    if drafted_user.id == ctx.bot.get_me().id:
        await ctx.respond(
            embed=hikari.Embed(
                title="Nope!",
                description="Sorry, can't draft me!"
            )
        )
        return
    
    await ctx.respond(
        hikari.Embed(
            title=f"{drafted_user.username} Has been drafted!",
            description=f"{drafted_user.username} Will be informed shortly that they are expected to help with this task."
        )
    )

    task = dataMan().get_todo_items(identifier=task_id)[task_id]
    contributor_count = len(dataMan().get_contributors(task_id))
    task_summary = f"{task['name']} - Task ID {task_id}\n{task['description']}\n\nThere are currently {contributor_count} others helping with this task."
    draft_embed = (
        hikari.Embed(
            title="Help Required!",
            description=f"{ctx.author.mention} Has assigned you to begin helping with a task."
        )
        .add_field(
            name="Task Details",
            value=task_summary
        )
        .add_field(
            name="Other",
            value="For more information, use /view (task id)"
        )
    )

    success = dataMan().mark_user_as_contributing(ctx.author.id, task_id, ctx.guild_id)
    if success is False:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="We failed to add the user as a contributor!"
            )
        )
        return
    if success == -1 or success == -2 or success == -3:
        await ctx.respond(
            hikari.Embed(
                title="Invalid",
                description="The user is either already contributing, not allowed to contribute, or the task is in another server."
            )
        )

    try:
        await drafted_user.send(draft_embed)
    except (hikari.ForbiddenError, hikari.UnauthorizedError):
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description=f"We were unable to inform the {drafted_user.username} that they were assigned to help!"
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
