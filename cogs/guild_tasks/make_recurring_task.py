from library.live_task_channel import livetasks
from cogs.guild_tasks.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='template_id',  # TODO: Make this compatible with NAMES and not just IDs, then change the name and desc.
    description="What's the ID of the template you want to use?",
    required=True,
    type=hikari.OptionType.STRING
)
@lightbulb.option(
    name='interval',
    description="How often do you want to repeat the task in days?",
    required=True,
    type=hikari.OptionType.INTEGER
)
@lightbulb.option(
    name='create_now',
    description="Create it now or in the future?",
    required=False,
    type=hikari.OptionType.BOOLEAN,
    default=True
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='recurring', description="Create a recurring task from a template.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create_cmd(ctx: lightbulb.SlashContext):
    template_name = ctx.options.template_id
    create_now = ctx.options.create_now
    interval = ctx.options.interval

    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    data = dataMan()

    # If the template doesn't exist, don't create the task
    template_count = len(data.get_task_template(template_name, int(ctx.guild_id)))
    if template_count == 0:
        await ctx.respond(
            hikari.Embed(
                title="Template not found",
                description="The template you specified does not exist."
            )
        )
        return

    recur_id = data.add_recurring_item(
        guild_id=ctx.guild_id,
        interval=interval,
        template_id=template_name,
        user_blame_id=ctx.author.id,
        get_recur_id=True
    )
    if create_now:
        task_id = data.create_task_from_template(
            guild_id=ctx.guild_id,
            template_id=template_name,
            task_creator_id=ctx.author.id,
            return_ticket=True
        )
        await livetasks.update_for_guild(ctx.guild_id)

        dataMan().update_last_recur(recur_id=recur_id, task_id=task_id)

    if recur_id is not False:  # Returns as bool False on fail.
        embed = (
            hikari.Embed(
                title="Recurring Task created!",
                description=f"Your recurring task has been created from the template you specified{"."
                if create_now else " but it won't be created until the next interval."}"
            )
        )
    else:
        embed = (
            hikari.Embed(
                title="Failed to create task!",
                description="Sorry, something went wrong!"
            )
        )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)

def unload(bot):
    bot.remove_plugin(plugin)
