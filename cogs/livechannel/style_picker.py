from library.live_task_channel import livetasks
from cogs.livechannel.group import group
from library.botapp import miru_client
from library.storage import dataMan
import lightbulb
import hikari
import miru

plugin = lightbulb.Plugin(__name__)

style_choices = ['classic', 'minimal', 'pinned', 'compact', 'pinned-minimal']

dm = dataMan()

class style_select_view(miru.View):
    @miru.text_select(
        placeholder="Select a style",
        options=[
            miru.SelectOption(label=style.capitalize(), value=style.lower()) for style in style_choices
        ],
        custom_id='style_select',
    )
    async def get_text(self, viewctx: miru.ViewContext, select: miru.text_select) -> None:
        success:bool = dm.set_livechannel_style(str(select.values[0]), int(viewctx.guild_id))

        if success:
            await viewctx.edit_response(
                hikari.Embed(
                    title="Style selected",
                    description=f"Style set to {select.values[0]}.",
                    color=plugin.bot.d['colourless']
                ),
                components=[],  # Remove the view
                flags=hikari.MessageFlag.EPHEMERAL
            )
        else:
            await viewctx.edit_response(
                hikari.Embed(
                    title="Error",
                    description="An error occurred while setting the style :(",
                    color=0xFF0000
                ),
                components=[],
                flags=hikari.MessageFlag.EPHEMERAL
            )

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

        view = style_select_view()

        await ctx.respond(
            embed, components=view, flags=hikari.MessageFlag.EPHEMERAL
        )
        miru_client.start_view(view)

        try:
            await view.wait_for_input(30)
        except TimeoutError:
            await ctx.edit_last_response(
                hikari.Embed(
                    title="Timed out",
                    description="You took too long to select a style.",
                    color=0xFF0000
                ),
                components=[],
            )
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

    await livetasks.update(guild_id=ctx.guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
