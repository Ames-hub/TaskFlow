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
    description="What's the ID of the task you want to mark as done?",
    required=True,
    type=hikari.OptionType.INTEGER
)
@lightbulb.command(name='complete', description="Use this command to complete a task", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, task_id:int):
    dm = dataMan()

    success = dm.mark_todo_finished(
        guild_id=int(ctx.guild_id),
        name_or_id=int(task_id),
    )

    if success:
        await ctx.respond(
            hikari.Embed(
                title="Task complete!",
                description=f"Task {task_id} has been marked as done. Nice."
            )
        )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Failed to complete task!",
                description="Sorry, something went wrong!"
            )
        )

    await livetasks.update(int(ctx.guild_id))


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
