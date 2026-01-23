from library.live_task_channel import livetasks
from cogs.task_incharge.group import group
from library.storage import dataMan
from library import shared
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='message',
    description="What's being announced?",
    type=hikari.OptionType.STRING,
    required=True,
    default=None
)
@lightbulb.option(
    name='task_id',
    description='Enter the task ID to announce for',
    type=hikari.OptionType.INTEGER,
    required=True,
    default=None
)
@lightbulb.command(name='announce', description="Announce to the members contributing to a task some information", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext, message, task_id):
    task_incharge = dataMan().get_task_incharge(task_id)
    if not task_incharge:
        embed = shared.get_no_incharge_embed()
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    if task_incharge != ctx.author.id:
        embed = shared.get_not_incharge_embed()
        await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)
        return
    
    await ctx.respond(
        hikari.Embed(
            title="Sending...",
            description="Making the announcement now!"
        )
    )

    contributors_list = dataMan().get_contributors(task_id)

    await livetasks.task_announcement(ctx.guild_id, message, contributors_list, task_id, ctx.author.id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
