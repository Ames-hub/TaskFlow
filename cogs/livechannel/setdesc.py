from cogs.livechannel.views.set_desc_view import SetDescModal
from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.botapp import miru_client
from library.storage import dataMan
from library.perms import perms
from library import tferror
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)
dm = dataMan()

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='description', # Can use this option as a fast-track to the view
    description="What do you want the desc to be for the live-list?",
    type=hikari.OptionType.STRING,
    required=False,
    default=None
)
@lightbulb.add_checks(
    lightbulb.guild_only
)
@lightbulb.command(name='setdesc', description="Set a description for your live list.", pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext, description:str):
    allowed = await perms.is_privileged(
        guild_id=ctx.guild_id,
        user_id=ctx.author.id,
        permission=dm.get_guild_configperm(ctx.guild_id)
    )
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, missing_perm="Manage Server")
        return

    if description is None:
        modal = SetDescModal()
        builder = modal.build_response(miru_client)
        await builder.create_modal_response(ctx.interaction)
        miru_client.start_modal(modal)
    else:
        success = dm.set_livelist_description(description.strip(), ctx.guild_id)

        if success:
            await ctx.respond(
                hikari.Embed(
                    title="Description set",
                    description="The description has been successfully set to what you entered."
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )
        else:
            await ctx.respond(
                hikari.Embed(
                    title="Uh oh!",
                    description="Something went wrong and we couldn't do it! :( We're tracking the error now."
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )
            return

    try:
        await livetasks.update_for_guild(int(ctx.guild_id))
    except tferror.livelist.no_channel:
        pass

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
