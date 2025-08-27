from library.live_task_channel import livetasks
from library.parsing import parse_deadline
from cogs.guild_tasks.group import group
from library.storage import dataMan
from library.perms import perms
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
)
@lightbulb.option(
    name='name',
    description='What name do you want to give the item?',
    required=True,
    type=hikari.OptionType.STRING
)
@lightbulb.add_checks(
    lightbulb.guild_only
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

    if task_name == "*":
        await ctx.respond(
            hikari.Embed(
                title="Task name cannot be '*'",
                description="You can't name your task '*'. That's reserved."
            )
        )
        return
    if len(task_name) > plugin.bot.d['max_name_length']:
        await ctx.respond(
            hikari.Embed(
                title="Task name too long!",
                description=f"Task names cannot be longer than {plugin.bot.d['max_name_length']} characters."
            )
        )
        return
    if len(task_desc) > plugin.bot.d['max_desc_length']:
        await ctx.respond(
            hikari.Embed(
                title="Task description too long!",
                description=f"Task descriptions cannot be longer than {plugin.bot.d['max_desc_length']} characters."
            )
        )
        return

    deadline_obj = parse_deadline(deadline_date, deadline_hmp)
    if isinstance(deadline_obj, str):
        await ctx.respond(
            hikari.Embed(
                title="Task deadline error!",
                description=deadline_obj  # Deadline obj is an error message on fail
            )
        )
        return

    data = dataMan()

    if category is not None:
        category_exists = data.get_category_exists(category)
    else:
        category_exists = False

    task_id = data.add_todo_item(
        guild_id=ctx.guild_id,
        name=task_name,
        description=task_desc,
        added_by=ctx.author.id,
        deadline=deadline_obj,
        category=category,
        return_task_id=True
    )

    embed = (
        hikari.Embed(
            title=f"New task added! ({task_id})",
            description=f"**Name:** {task_name} | ID: {task_id}\n**Description:** {task_desc}\n"
                        f"**Deadline:** {deadline_obj}\n" if deadline_obj else ""
                        f"**Category:** {category}" if category else ""
        )
    )
    if category_exists is False and category is not None:
        embed.add_field(
            name="Category added!",
            value=f"The category '{category}' has been added to your list of categories."
        )

    await ctx.respond(embed)
    await livetasks.update_for_guild(ctx.guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)
