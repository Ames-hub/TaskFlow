from cogs.livechannel.views.style_sel_view import view as styleview
from cogs.livechannel.group import group
from library.botapp import miru_client
from library.storage import dataMan
from library.perms import perms
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

# Reminder: On modification, also update style_sel_view.py
style_choices = ['classic', 'minimal', 'pinned', 'compact', 'pinned-minimal']

dm = dataMan()

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.option(
    name='style', # Can use this option as a fast-track to the view
    description="What style do you want to use?",
    type=hikari.OptionType.STRING,
    choices=style_choices,
    required=False,
)
@lightbulb.command(name='textstyle', description="Designate a live channel for your servers tasks.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    allowed = await perms.is_privileged(
        guild_id=ctx.guild_id,
        user_id=ctx.author.id,
        permission=dm.get_guild_configperm(ctx.guild_id)
    )
    if not allowed:
        await perms.embeds.insufficient_perms(ctx, missing_perm="Manage Server")
        return

    style: hikari.GuildChannel = ctx.options.style

    if not style:
        embed = (
            hikari.Embed(
                title="Select a style",
                description="Choose a style for your live channel.",
                color=plugin.bot.d['colourless']
            )
            .add_field(
                name="Classic",
                value="The classic style for live channels."
            )
            .add_field(
                name="Minimal",
                value="Few details, more focused on the main content."
            )
            .add_field(
                name="Pinned",
                value="In the style of a bulletin markdown list."
            )
            .add_field(
                name="Compact",
                value="Detailed, but compact."
            )
            .add_field(
                name="Pinned minimal",
                value="A pinned style mixed with a minimalistic style."
            )
            .set_thumbnail(ctx.bot.get_me().avatar_url)
        )

        view = styleview.style_select_view()

        await ctx.respond(
            embed, components=view, flags=hikari.MessageFlag.EPHEMERAL
        )
        miru_client.start_view(view)
        await view.wait()
    else:
        success = dm.set_livechannel_style(str(style), int(ctx.guild_id))

        if success:
            await ctx.respond(
                hikari.Embed(
                    title="Style selected",
                    description=f"Style set to {style}.",
                    color=plugin.bot.d['colourless']
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )
        else:
            await ctx.respond(
                hikari.Embed(
                    title="Error",
                    description="An error occurred while setting the style :(",
                    color=0xFF0000
                ),
                flags=hikari.MessageFlag.EPHEMERAL
            )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
