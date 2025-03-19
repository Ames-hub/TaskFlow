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
@lightbulb.command(name='contribute', description="Contribute to a task", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, task_id:int):
    dm = dataMan()

    success = dm.mark_user_as_contributing(
        guild_id=int(ctx.guild_id),
        task_id=int(task_id),
        user_id=int(ctx.author.id)
    )

    if success:
        await ctx.respond(
            hikari.Embed(
                title="Now contributing to task!",
                description=f"You are now contributing to task {task_id}."
            )
        )
    elif success == -1:
        await ctx.respond(
            hikari.Embed(
                title="Already contributing!",
                description="You're already contributing to that task."
            )
        )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Sorry, something went wrong while trying to do that!"
            )
        )

    await livetasks.update(int(ctx.guild_id))

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
