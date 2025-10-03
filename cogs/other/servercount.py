from library.storage import get_member_total_count
import lightbulb
import datetime
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='servercount', description='Get a number of servers the bot is in.')
@lightbulb.implements(lightbulb.SlashCommand)
async def server_count(ctx: lightbulb.SlashContext):
    # A basic cache system to prevent spamming the API
    if ctx.bot.d['servercount_memory']['last_updated'] is not None:
        if ctx.bot.d['servercount_memory']['last_updated'] - datetime.datetime.now() < datetime.timedelta(hours=1):
            count = ctx.bot.d['servercount_memory']['count']
        else:
            my_guilds = await ctx.bot.rest.fetch_my_guilds()
            count = len(my_guilds)
            ctx.bot.d['servercount_memory']['last_updated'] = datetime.datetime.now()
            ctx.bot.d['servercount_memory']['count'] = count
    else:
        my_guilds = await ctx.bot.rest.fetch_my_guilds()
        count = len(my_guilds)
        ctx.bot.d['servercount_memory']['last_updated'] = datetime.datetime.now()
        ctx.bot.d['servercount_memory']['count'] = count

    embed = (
        hikari.Embed(
            title="Server Count",
            description=f"I'm in {count} servers!"
        )
    )

    total_members = ctx.bot.d.get("total_members_memory", -1)
    if total_members == -1:
        total_members = get_member_total_count()
    embed.add_field(
        name="Total Members",
        value=f"{total_members}",
    )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
