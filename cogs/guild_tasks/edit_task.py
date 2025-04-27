from cogs.guild_tasks.views.edit_task_menu import main_view, init_edit_modal
from cogs.guild_tasks.group import group
from library.botapp import miru_client
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='task_id',
    description="What's the task ID?",
    required=False,
    default=None,
    type=hikari.OptionType.INTEGER
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='edit', description='Edit a task', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def edit_task_cmd(ctx: lightbulb.SlashContext, task_id:int=None):
    view = main_view(int(ctx.guild_id))
    viewmenu = view.init_view()

    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    if task_id is not None:
        modal = init_edit_modal(task_id=task_id)
        builder = modal.build_response(miru_client)
        await builder.create_modal_response(ctx.interaction)
        miru_client.start_modal(modal)
        return

    if len(view.task_data) >= 25:
        for item in view.task_data:
            item = view.task_data[item]
            if item['id'] == task_id:
                modal = init_edit_modal(task_id=task_id)
                builder = modal.build_response(miru_client)
                await builder.create_modal_response(ctx.interaction)
                miru_client.start_modal(modal)
                return
        else:
            await ctx.respond(
                embed=hikari.Embed(
                    title="No task found!",
                    description="Sorry, that task doesn't exist."
                )
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
