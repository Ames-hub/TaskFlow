from cogs.task_templates.views.template_deletion_confirm import main_view
from cogs.task_templates.group import group
from library.botapp import miru_client
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='identifier',
    description="*The numerical ID of the template you want to delete.",
    required=True,
    type=hikari.OptionType.INTEGER,
    min_value=0,
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='delete', description="Delete a template.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create_cmd(ctx: lightbulb.SlashContext, identifier):
    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    embed = (
        hikari.Embed(
            title="Template Deletion",
            description="Confirmation: Do you want to delete this template?\n**Doing so will delete all tasks that use this template.**"
        )
    )

    view = main_view(template_id=int(identifier))
    viewmenu = view.init_view()
    await ctx.respond(embed=embed, components=viewmenu.build(), flags=hikari.MessageFlag.EPHEMERAL)
    miru_client.start_view(viewmenu)
    await viewmenu.wait()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
