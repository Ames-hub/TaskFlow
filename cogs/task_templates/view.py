from cogs.task_templates.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='identifier',
    description="*The name or ID of the template you want to view.",
    required=True,
    type=hikari.OptionType.STRING,
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='view', description="View a template's details.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def get_template(ctx: lightbulb.SlashContext, identifier):
    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    template_data = dataMan().get_task_template(identifier=identifier, guild_id=ctx.guild_id)

    if len(template_data['task_desc']) != 0:
        description_txt = f"**Task Description:** {template_data['task_desc']}\n"
    else:
        description_txt = ""

    await ctx.respond(
        hikari.Embed(
            title=f"({template_data['id']}) Template: {template_data['name']}",
            description=f"**Name:** {template_data['task_name']}\n{description_txt}"
                        f"**Category:** {template_data['task_category']}\n"
                        f"**Deadline:** {template_data['task_deadline']}\n"
        ),
        flags=hikari.MessageFlag.EPHEMERAL
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
