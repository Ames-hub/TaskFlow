from cogs.guild_permissions.group import group
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='discover', description='Find out what your permission level is', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext):
    perm = perms()
    dm = dataMan()

    can_interact = await perm.can_interact_tasks(user_id=ctx.author.id, guild_id=ctx.guild_id)

    embed = (
        hikari.Embed(
            title="Permissions Discovery",
            description="Your current authentication level is as described.",
        )
    )
    if can_interact:
        embed.add_field(
            name="Can interact with tasks",
            value="You can create, delete, edit, complete and contribute to any task."
        )
    else:
        helper_role_id = dm.get_taskmaster_role(guild_id=ctx.guild_id)
        embed.add_field(
            name="Cannot interact with tasks",
            value=f"You can't create, delete, edit, etc. any task.\nOnly the <@&{helper_role_id}> role can interact."
        )

    can_configure_bot = perms.can_configure_bot(ctx.guild_id, ctx.author.id)

    if can_configure_bot:
        embed.add_field(
            name="You can Configure the Bot",
            value="All bot configuration commands are open to your access."
        )
    else:
        embed.add_field(
            name="You cannot configure the bot",
            value="The bot configuration's need a higher permission level."
        )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
