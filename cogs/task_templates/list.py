from cogs.task_templates.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='list', description="List all templates for the server.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def list_cmd(ctx: lightbulb.SlashContext):
    if await perms().can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id) is False:
        await ctx.respond(
            embed=perms.embeds.gen_interaction_tasks_embed(),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return

    dm = dataMan()
    temp_list = dm.get_task_template("*", guild_id=ctx.guild_id)
    if temp_list is False:
        await ctx.respond(
            embed=hikari.Embed(
                title="Something went wrong!",
                description="Sorry, we'll try to find out what went wrong and fix it. Please try again later!"
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    elif temp_list is None:
        temp_list = {}

    efield = ""
    if len(temp_list) == 0:
        efield = "You don't have any templates yet!\nUse /template create to create one."
    else:
        for template_id in temp_list.keys():
            template = temp_list[template_id]
            efield += f"**{template['id']}** - {template['name']}\n\n"

    embed = hikari.Embed(
        title="Task Templates",
        description=f"Here are the templates you have created.\n\n{efield}"
    )

    await ctx.respond(
        embed=embed,
        flags=hikari.MessageFlag.EPHEMERAL
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
