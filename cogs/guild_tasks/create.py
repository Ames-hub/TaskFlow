from library.live_task_channel import livetasks
from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='description',
    description="What's the task? Describe here in as much detail as you like.",
    required=False,
    default='...'
)
@lightbulb.option(
    name='name',
    description='What name do you want to give the item?',
)
@lightbulb.command(name='create', description='Create an item for your guild\'s to-do list.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create_cmd(ctx: lightbulb.SlashContext):
    task_name = ctx.options.name
    task_desc = ctx.options.description

    data = dataMan()
    data.add_todo_item(
        guild_id=ctx.guild_id,
        name=task_name,
        description=task_desc,
        added_by=ctx.author.id
    )

    await ctx.respond("Your task has been added to the guild to-do list!")
    await livetasks.update(ctx.guild_id)
def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
