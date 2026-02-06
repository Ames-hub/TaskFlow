from library.storage import dataMan
from library.perms import perms
import lightbulb
import datetime
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='taskstats', description="View your server's task stats", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def command(ctx: lightbulb.SlashContext):
    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    dm = dataMan()

    all_tasks = dm.get_todo_items(guild_id=ctx.guild_id, filter_for="*")
    pending_tasks = {}
    completed_tasks = {}
    for task in all_tasks:
        task = all_tasks[task]
        if task["completed"] == False:
            pending_tasks[task["uid"]] = task
        else:
            completed_tasks[task["uid"]] = task

    comp_txt = ""
    pending_txt = ""
    waiting_txt = ""
    for task in all_tasks:
        task = all_tasks[task]
        emoji = "✅" if task['completed'] is True else "❌"
        if task['completed']:
            comp_txt += f"{emoji} ({task['uid']}) {task['name']}\n"
        else:
            contrib_count = len(dm.get_contributors(task_id=task['uid']))
            if task['add_date'] != None:
                date = datetime.datetime.strptime(
                    task['add_date'],
                    "%Y-%m-%d %H:%M:%S.%f%z"
                ).strftime("%Y/%m/%d")
                date_txt = f" — {date}"
            else:
                date_txt = ""
            
            if contrib_count > 0: 
                pending_txt += f"{emoji} ({task['uid']}) {task['name']}{date_txt}\n"
            else:
                waiting_txt += f"⚠️ ({task['uid']}) {task['name']}{date_txt}\n"

    embed = (
        hikari.Embed(
            title="Task Statistics",
            description=f"{len(completed_tasks)}/{len(pending_tasks)} Done | You have {len(pending_tasks)} tasks remaining"
        )
        .add_field(
            name="Completed",
            value=comp_txt,
            inline=True
        )
        .add_field(
            name="Pending",
            value=pending_txt,
            inline=True
        )
        .add_field(
            name="Waiting!",  # For tasks with no contributors
            value="These tasks are not being worked on\n\n" + waiting_txt
        )
    )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
