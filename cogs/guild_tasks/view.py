from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb
import datetime
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='name_or_id',
    description='What is the name or ID for the task you want to view?',
    required=False,
    default=None
)
@lightbulb.command(name='view', description="View a tasks details.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def view_cmd(ctx: lightbulb.SlashContext):
    task_name = ctx.options['name_or_id']
    incompleted_task_list = dataMan().get_todo_items(
        guild_id=ctx.guild_id,
        identifier=task_name,
        filter_for='incompleted' if not task_name.isnumeric() else "*"
    )

    task_count = len(incompleted_task_list)
    if task_count != 1:
        desc_value = f"We found {task_count} tasks that meet the requested criteria."
    else:
        desc_value = None

    embed = (
        hikari.Embed(
            title="Found Tasks",
            description=desc_value,
        )
    )

    task_counter = 0
    for task in incompleted_task_list:
        name = task[0]
        description = task[1]
        completed = task[2]
        task_id = task[3]
        added_by = task[5]

        # If the task is completed, we want to show a different emoji.
        completed_text = f"Completed: {'❌' if not completed else '✅'}"
        # If there is no description, don't show the '...' placeholder. Just show completion.
        # Otherwise, show the description and the completion.
        desc_value = f"{description}\n\n{completed_text}" if description != "..." else completed_text
        desc_value += f"\nAdded by: <@{added_by}>"

        task_counter += 1
        embed.add_field(
            name=f'{task_counter}. {name}\n(ID: {task_id})',
            value=desc_value,
            inline=False
        )

    if task_counter != 1:
        # Pointless to track the msg if we don't know which one it is. So this makes it look marginally better.
        if task_counter != 0:
            embed.set_footer("There are too many tasks to track. Please use its ID to track a specific task.")
        await ctx.respond(
            embed,
            flags=hikari.MessageFlag.EPHEMERAL
        )
    else:
        # To prevent the 'app did not respond' error from showing up.
        embed.set_footer(
            "React with ✅ to mark this task as completed/incomplete. Unreact to undo.\n"
            "React with 🔔 to indicate you intend to contribute to the completion of this task."
        )
        # Doing this because for some reason ctx.respond doesn't let us have the msg id
        await ctx.respond("Please wait a moment, we're getting the data for you.", flags=hikari.MessageFlag.EPHEMERAL)
        msg = await ctx.bot.rest.create_message(channel=ctx.channel_id, embed=embed)
        plugin.bot.d['watched_messages'][msg.id] = [incompleted_task_list[0][3], ctx.guild_id]  # msg id, task id, guid

        # We remove 5 seconds so that the cooldown is not triggered.
        plugin.bot.d['last_edited'][msg.id] = datetime.datetime.now() - datetime.timedelta(seconds=5)
        await msg.add_reaction('✅')
        # Information mark to indicate "I'm gonna contribute to this task!"
        await msg.add_reaction('🔔')

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
