from library.live_task_channel import livetasks
from library.parsing import parse_deadline
from library.perms import perms
from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='deadline_hmp',
    description="Enter a specific time in the format: HH:MM AM/PM",
    type=hikari.OptionType.STRING,
    required=False,
    default=None
)
@lightbulb.option(
    name='deadline_date',
    description="Enter a specific date in the format: DD/MM/YYYY",
    type=hikari.OptionType.STRING,
    required=False,
    default=None
)
@lightbulb.option(
    name='category',
    description='What category does this item belong to?',
    required=False,
    default=None,
    type=hikari.OptionType.STRING
)
@lightbulb.option(
    name='description',
    description="What's the task? Describe here in as much detail as you like.",
    required=False,
    default='...',
    type=hikari.OptionType.STRING,
    max_length=2000
)
@lightbulb.option(
    name='name',
    description='What name do you want to give the item?',
    required=True,
    max_length=100,
    type=hikari.OptionType.STRING
)
@lightbulb.command(name='create', description='Create an item for your guild\'s to-do list.')
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create_cmd(ctx: lightbulb.SlashContext):
    task_name = ctx.options.name
    task_desc = ctx.options.description
    deadline_hmp = ctx.options.deadline_hmp
    deadline_date = ctx.options.deadline_date
    category = ctx.options.category

    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    deadline_obj = parse_deadline(deadline_date, deadline_hmp)
    if isinstance(deadline_obj, str):
        await ctx.respond(deadline_obj)
        return

    data = dataMan()

    if category is not None:
        category_exists = data.get_category_exists
    else:
        category_exists = False

    data.add_todo_item(
        guild_id=ctx.guild_id,
        name=task_name,
        description=task_desc,
        added_by=ctx.author.id,
        deadline=deadline_obj,
        category=category
    )

    await ctx.respond(f"{'New category created! and, ' if category_exists else ''}{'y' if category_exists else 'Y'}our task has been added to the guild to-do list!"
                      f"\n{f'We will remind you on {deadline_obj}' if deadline_obj else ''}")
    await livetasks.update(ctx.guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)
