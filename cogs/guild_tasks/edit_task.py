from cogs.guild_tasks.views.edit_task_menu import main_view
from library.perms import perms
from cogs.guild_tasks.group import group
from library.botapp import miru_client
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='edit', description='Edit a task', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def edit_task_cmd(ctx: lightbulb.SlashContext):
    view = main_view(int(ctx.guild_id))
    viewmenu = view.init_view()

    if perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    await ctx.respond(
        view.gen_init_embed(),
        components=viewmenu.build(),
        flags=hikari.MessageFlag.EPHEMERAL
    )

    miru_client.start_view(viewmenu)
    await viewmenu.wait()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
