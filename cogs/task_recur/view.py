from cogs.task_recur.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='task_id',
    description="What's an assosciated Task ID of the recurring task?",
    required=True,
    type=hikari.OptionType.INTEGER
)
@lightbulb.command(name='view', description='View a recurring task by an assosciated task ID', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, task_id: int):
    dm = dataMan()
    data = dm.get_recur_details_by_taskid(task_id)

    if data is False:
        await ctx.respond(
            hikari.Embed(
                title='Recurring Task 404',
                description="A Recur flag couldn't be found for that task."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    elif data['guild_id'] != ctx.guild_id:
        await ctx.respond(
            hikari.Embed(
                title='Forbidden',
                description="You cannot see this recurring task as it doesn't belong to your server."
            )
        )

    embed = (
        hikari.Embed(
            title='Recurring Task',
            description=f'Recur ID: {data['id']} | Template ID: {data['template_id']}\n'
                        f'Recurs every {'day' if data['interval'] == 1 else f"{data["interval"]} days"}.\n'
                        f'Blame ID: {data["blame_id"]} (<@{data["blame_id"]}>)',
        )
    )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
