from library.live_task_channel import livetasks
from cogs.guild_tasks.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='status',
    description="Do you want us to show the Red X on the live list?",
    required=True,
    type=hikari.OptionType.STRING,
    choices=['Yes', 'No']
)
@lightbulb.command(name='xtoggle', description='Toggle the Red X on the list', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext, status):
    dm = dataMan()
    status = status.lower()
    if status == "yes":
        status = True
    else:
        status = False

    success = dm.toggle_show_task_completion(status, guild_id=ctx.guild_id)

    if success is True:
        if status is True:
            await ctx.respond(
                hikari.Embed(
                    title="Done",
                    description="We'll now show the Red X on the live task list."
                )
            )
        else:
            await ctx.respond(
                hikari.Embed(
                    title="Done",
                    description="We'll now no longer show the Red X on the live task list."
                )
            )
    else:
        await ctx.respond(
            hikari.Embed(
                title="Uh oh!",
                description="Something went wrong? :("
            )
        )
        return

    await livetasks.update(ctx.guild_id)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
