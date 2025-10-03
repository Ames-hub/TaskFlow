from library.storage import set_member_count
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='countmembers', description='Get a number of the amount of members this server has.')
@lightbulb.implements(lightbulb.SlashCommand)
async def server_count(ctx: lightbulb.SlashContext):
    total_members = len(await plugin.bot.rest.fetch_members(ctx.guild_id))

    embed = (
        hikari.Embed(
            title='Total Members',
            description=f"{total_members} Counted.",
        )
    )

    await ctx.respond(embed)

    set_member_count(guild_id=ctx.guild_id, count=total_members)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
