from cogs.guild_permissions.group import group
from library.perms import perms
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='permission',
    description="Which permission do you need to configure the bot for the server?",
    required=True,
    type=hikari.OptionType.STRING,
    choices=['Administrator', 'Manage Server', 'none']
)
@lightbulb.command(name='configperm', description='Set which permission is used to enable configuration of the bot.', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd(ctx: lightbulb.SlashContext, permission:str):
    dm = dataMan()

    allowed = await perms.is_privileged(hikari.Permissions.ADMINISTRATOR, guild_id=ctx.guild_id, user_id=ctx.author.id)
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, 'administrator')
        return

    permission_crossref = {
        'administrator': hikari.Permissions.ADMINISTRATOR,
        'manage server': hikari.Permissions.MANAGE_GUILD,
        'none': None
    }

    success = dm.set_guild_configperm(ctx.guild_id, permission_crossref[permission])

    if success:
        await ctx.respond(
            embed=hikari.Embed(
                title="Success!",
                description="The configuration permission was set."
            )
        )
    else:
        await ctx.respond(
            embed=hikari.Embed(
                title="Uh oh!",
                description="Something didn't go right! We're tracking the error now."
            )
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
