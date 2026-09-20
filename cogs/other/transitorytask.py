from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)
@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.option(
    name="do_hide",
    description="True to hide yesterdays tasks, False to show all tasks.",
    type=hikari.OptionType.BOOLEAN,
    required=True
)
# @lightbulb.add_cooldown (cooldown here)
@lightbulb.command(name='transitorytasks', description="Choose to hide all tasks not from today.")
@lightbulb.implements(lightbulb.SlashCommand)
async def roadmap(ctx: lightbulb.SlashContext):
    do_hide = bool(ctx.options.do_hide)
    success = dataMan().make_guild_tasks_transitory(ctx.guild_id, do_hide)

    await ctx.respond(
        hikari.Embed(
            title="Transitory Status Changed",
            description=(
                "Tasks that are not from the current day will be hidden and marked complete in the live list."
                if do_hide else
                "All tasks from all days will be shown if applicable."
            )
        )
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
