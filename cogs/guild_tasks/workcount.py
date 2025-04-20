from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb
import hikari
import io

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='user',
    description='The user to count the amount of tasks contributed to.',
    required=False,
    type=hikari.OptionType.USER,
    default=None
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(
    name='workcount',
    description="Count the amount of tasks a user has contributed to.",
    pass_options=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def workcount_cmd(ctx: lightbulb.SlashContext, user: hikari.User = None):
    user = user or ctx.author
    guild_id = ctx.guild_id
    user_id = user.id

    contrib_tasks: dict = dataMan().get_user_contributions(user_id=int(user_id), guild_id=int(guild_id))

    task_contrib_msg = ""

    for task_id in contrib_tasks:
        task = contrib_tasks[task_id]
        desc = task['description']
        task_contrib_msg += (f"Name: **{task['name']}** ({task_id})\n"
                             f"{desc if desc != '...' else "No description"}\n"
                             f"Completed: {'✅' if task['completed'] else '❌'}\n"
                             f"\n")

    datafile = None
    if task_contrib_msg == "":
        task_contrib_msg = "This user has not contributed to any tasks in present or past."
    elif len(task_contrib_msg) > 2000:
        datafile = io.BytesIO(task_contrib_msg.encode("utf-8"))
        task_contrib_msg = "This user has or is contributing to too many tasks to display here. Sending file..."

    embed = (
        hikari.Embed(
            title="Data retrieved.",
            description=f"{len(contrib_tasks)} Tasks are being contributed to by {user.username}",
        )
    )
    if task_contrib_msg != "This user has not contributed to any tasks.":
        embed.add_field(
            name="Tasks:",
            value=task_contrib_msg,
            inline=False
        )

    attachment = None
    if datafile is not None:
        attachment = hikari.Bytes(
            datafile,
            "tasks_contributed.txt",
            mimetype="text/plain"
        )

    await ctx.respond(embed=embed, attachment=attachment)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
