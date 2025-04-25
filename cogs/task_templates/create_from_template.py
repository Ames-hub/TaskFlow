from library.live_task_channel import livetasks
from cogs.task_templates.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='template_name_or_id',
    description="The name or ID of the template you want to use.",
    required=True,
    type=hikari.OptionType.STRING,
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='make_task', description="Create a task from a template", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def create_cmd(ctx: lightbulb.SlashContext, template_name_or_id):
    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    dm = dataMan()
    success = dm.create_task_from_template(
        guild_id=ctx.guild_id,
        template_id=template_name_or_id,
        task_creator_id=ctx.author.id
    )

    if success:
        await ctx.respond(
            embed=hikari.Embed(
                title="Task created!",
                description="Your task has been created from the template you specified."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        await livetasks.update_for_guild(ctx.guild_id)
    elif success == -1:
        await ctx.respond(
            embed=hikari.Embed(
                title="Wrong Server",
                description="You must be in the same server as the template!"
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
    elif success is None:
        await ctx.respond(
            embed=hikari.Embed(
                title="Template not found",
                description="The template you specified was not found."
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
    else:
        await ctx.respond(
            embed=hikari.Embed(
                title="Uh oh!",
                description="Something went wrong and we couldn't do it! :("
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
