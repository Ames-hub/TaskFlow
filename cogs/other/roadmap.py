import lightbulb

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=False)
# @lightbulb.option (options here)
# @lightbulb.add_cooldown (cooldown here)
@lightbulb.command(name='roadmap', description="What's planned? Find out here!")
@lightbulb.implements(lightbulb.SlashCommand)
async def roadmap(ctx: lightbulb.SlashContext):
    msg = (
        "The current roadmap as of 16/07/2024 is as follows:\n"
        "1. Add 'assigning task' functionality.\n"
        "2. Add 'deadline' Alerts and ability to set deadlines/timers on tasks.\n"
        "3. Fix the little [] that appears in the live task list after a task has been completed/uncompleted. "
        "I could fix it now, but its 4 am as I write this. So no. Until further notice, its a feature. Not a bug.\n"
        "4. Add ability to edit tasks.\n"
        "5. Add ability to delete tasks instead of just moving them to an 'archive' of sorts.\n"
        "6. Implementing a personal tasks list. Not just for the server.\n"
        "\nIf you have any features you'd like to see, run /github, go to the link and open a pull request! ^^"
    )
    await ctx.respond(msg)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
