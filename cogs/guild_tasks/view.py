from cogs.guild_tasks.views.viewcmd_view import view_cmd_view
from cogs.guild_tasks.group import group
from library.botapp import miru_client
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='name_or_id',
    description='What is the name or ID for the task you want to view?',
    required=True,
    default=None
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='view', description="View a tasks details.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def view_cmd(ctx: lightbulb.SlashContext):
    task_identifier = ctx.options['name_or_id']

    try:
        view = view_cmd_view(task_id=task_identifier, guild_id=int(ctx.guild_id))
    except IndexError:
        await ctx.respond(
            hikari.Embed(
                title="Too many tasks",
                description="Sorry, too many tasks are under that name to view by name."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    data = view.generate_task_embed(int(ctx.author.id))
    task_counter = data['task_c']
    embed:hikari.Embed = data['embed']
    attachment = data['attached']

    if task_counter != 1:
        if task_counter != 0:
            embed.add_field(
                name="Too many tasks.",
                value="There are too many tasks to track. Please use its ID to track the specific task."
            )
        await ctx.respond(
            embed,
            flags=hikari.MessageFlag.EPHEMERAL,
            attachment=attachment
        )
    else:
        viewmenu = await view.init_view(user_id=ctx.author.id)
        await ctx.respond(flags=hikari.MessageFlag.EPHEMERAL, embed=embed, components=viewmenu.build(), attachment=attachment)
        miru_client.start_view(viewmenu)
        await viewmenu.wait()

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
