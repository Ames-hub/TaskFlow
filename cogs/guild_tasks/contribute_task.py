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
    description="What's the ID of the task you want to mark as done?",
    required=True,
    type=hikari.OptionType.INTEGER
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='contribute', description="Contribute to a task", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, task_id:int):
    dm = dataMan()

    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    success = dm.mark_user_as_contributing(
        guild_id=int(ctx.guild_id),
        task_id=int(task_id),
        user_id=int(ctx.author.id)
    )

    if success is True:
        await ctx.respond(
            hikari.Embed(
                title="Now contributing to task!",
                description=f"You are now contributing to task {task_id}."
            )
        )
        await livetasks.update_for_guild(int(ctx.guild_id))
    elif success == -1:
        await ctx.respond(
            hikari.Embed(
                title="Already contributing!",
                description="You're already contributing to that task."
            )
        )
    elif success == -2:
        await ctx.respond(
            hikari.Embed(
                title="Late contribution",
                description="The task is completed, late contribution is not allowed on this server."
            )
        )
    elif success == -3:
        await ctx.respond(
            hikari.Embed(
                title="Wrong Server",
                description="That's not a task for this server!"
            )
        )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Sorry, something went wrong while trying to do that!"
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
