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
    type=hikari.OptionType.STRING
)
@lightbulb.option(
    name='name',
    description='What name do you want to give the item?',
    required=True,
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

    deadline_hmp_obj = None
    deadline_date_obj = None
    if deadline_hmp is not None:
        time_set = str(deadline_hmp[:-3]).replace(':', '')
        if not time_set.isnumeric() or len(time_set) != 4:
            await ctx.respond("Please enter a valid time in the format: HH:MM AM/PM, eg: 05:30 PM")
            return
        elif " " not in deadline_hmp:
            await ctx.respond("There must be a space in-between HH:MM and AM/PM. Eg: 05:30 PM")
            return
        elif not deadline_hmp[-2:].lower() in ['am', 'pm']:
            await ctx.respond("You did not enter AM or PM. Please use this example: 05:30 PM")
            return
        elif not deadline_hmp[:-3].replace(':', '').isnumeric():
            await ctx.respond("Please enter a valid time in the format: HH:MM AM/PM, eg: 05:30 PM")
            return
        elif int(time_set) > 1259 or int(time_set) < 100:
            await ctx.respond("The range for the time is between 01:00 AM and 12:59 PM. Please enter a valid time.")
            return
        deadline_hmp_obj = datetime.strptime(deadline_hmp, "%I:%M %p")

    if deadline_date is not None:
        date_set = deadline_date.replace('/', '')
        if not date_set.isnumeric():
            await ctx.respond("Please enter a valid date in the format: DD/MM/YYYY, eg 05/11/2025")
            return
        elif len(date_set) != 8:
            await ctx.respond("Please enter a valid date in the format: DD/MM/YYYY, eg 05/11/2025")
            return
        elif str(date_set)[:2] not in [
            "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"
            ]:
            await ctx.respond(f"Please enter a valid day between 01 and 31. You entered, {str(date_set)[:2]}")
            return
        elif str(date_set)[2:4] not in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
            await ctx.respond(f"Please enter a valid month between 01 and 12. You entered, {str(date_set)[2:4]}")
            return
        deadline_date_obj = datetime.strptime(deadline_date, "%d/%m/%Y")

    if deadline_hmp_obj is not None and deadline_date_obj is not None:
        deadline_obj = deadline_date_obj.replace(hour=deadline_hmp_obj.hour, minute=deadline_hmp_obj.minute, second=deadline_hmp_obj.second)
    elif deadline_date_obj is not None:
        deadline_obj = deadline_date_obj
    elif deadline_hmp_obj is not None:
        await ctx.respond("Please enter a date to go with the time.")
        return
    elif deadline_date is None and deadline_hmp is None:
        deadline_obj = None
    else:
        await ctx.respond(
            "Something went wrong with the logic of setting the deadline.\n"
            "DEBUG INFO:\n"
            f"deadline_hms_obj: {deadline_hmp_obj} | {type(deadline_hmp_obj)}\n"
            f"deadline_date_obj: {deadline_date_obj} | {type(deadline_date_obj)}\n"
            f"deadline_hmp: {deadline_hmp} | {type(deadline_hmp)}\n"
            f"deadline_date: {deadline_date} | {type(deadline_date)}"
        )
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
                      f"\n{f"We will remind you on {deadline_obj}" if deadline_obj else ''}")
    await livetasks.update(ctx.guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
