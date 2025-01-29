from library.live_task_channel import livetasks
from cogs.guild_tasks.group import group
from library.storage import dataMan
from datetime import datetime
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='deadline_hms',
    description="Enter a specific time in the format: HH:MM:SS",
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
    deadline_hms = ctx.options.deadline_hms
    deadline_date = ctx.options.deadline_date

    deadline_hms_obj = None
    deadline_date_obj = None
    if deadline_hms is not None:
        if not deadline_hms.replace(':', '').isnumeric():
            await ctx.respond("Please enter a valid time in the format: HH:MM:SS")
            return
        deadline_hms_obj = datetime.strptime(deadline_hms, "%H:%M:%S")

    if deadline_date is not None:
        if not deadline_date.replace('/', '').isnumeric():
            await ctx.respond("Please enter a valid date in the format: DD/MM/YYYY")
            return
        deadline_date_obj = datetime.strptime(deadline_date, "%d/%m/%Y")

    if deadline_hms_obj is not None and deadline_date_obj is not None:
        deadline_obj = deadline_date_obj.replace(hour=deadline_hms_obj.hour, minute=deadline_hms_obj.minute, second=deadline_hms_obj.second)
    elif deadline_date_obj is not None:
        deadline_obj = deadline_date_obj
    elif deadline_hms_obj is not None:
        await ctx.respond("Please enter a date to go with the time.")
        return
    elif deadline_date is None and deadline_hms is None:
        deadline_obj = None
    else:
        await ctx.respond(
            "Something went wrong with the logic of setting the deadline.\n"
            "DEBUG INFO:\n"
            f"deadline_hms_obj: {deadline_hms_obj} | {type(deadline_hms_obj)}\n"
            f"deadline_date_obj: {deadline_date_obj} | {type(deadline_date_obj)}\n"
            f"deadline_hms: {deadline_hms} | {type(deadline_hms)}\n"
            f"deadline_date: {deadline_date} | {type(deadline_date)}"
        )
        return

    data = dataMan()
    data.add_todo_item(
        guild_id=ctx.guild_id,
        name=task_name,
        description=task_desc,
        added_by=ctx.author.id,
        deadline=deadline_obj
    )

    await ctx.respond("Your task has been added to the guild to-do list!"
                      f"\n{f"We will remind you on {deadline_obj}" if deadline_obj else ''}")
    await livetasks.update(ctx.guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
