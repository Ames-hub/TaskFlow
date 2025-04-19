from cogs.task_templates.views.template_maker_view import main_view
from cogs.task_templates.group import group
from library.botapp import miru_client
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='create', description="Create a template.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create_cmd(ctx: lightbulb.SlashContext):
    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    view = main_view()
    viewmenu = view.init_view()
    await ctx.respond(flags=hikari.MessageFlag.EPHEMERAL, embed=view.gen_initial_embed(), components=viewmenu.build())
    miru_client.start_view(viewmenu)
    await viewmenu.wait()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
