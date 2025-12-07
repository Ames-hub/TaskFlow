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
    description="What's the ID of the task you want to mark as done?",
    required=True,
    type=hikari.OptionType.INTEGER
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='uncomplete', description="Use this command to mark a task as incomplete", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, task_id:int):
    dm = dataMan()

    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    if dm.crossref_task(task_id) != int(ctx.guild_id):
        await ctx.respond(
            hikari.Embed(
                title="Wrong Server!",
                description="That's a task for another server!"
            )
        )
        return

    success = dm.mark_todo_not_finished(
        guild_id=int(ctx.guild_id),
        name_or_id=int(task_id),
    )

    if success:
        await ctx.respond(
            hikari.Embed(
                title="Task marked incomplete.",
                description=f"Task {task_id} has been marked as done. Nice."
            )
        )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Failed to mark task as incomplete!",
                description="Sorry, something went wrong!"
            )
        )

    await livetasks.update_for_guild(int(ctx.guild_id))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
