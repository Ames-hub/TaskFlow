from library.storage import get_member_total_count, count_all_servers_and_members
import lightbulb
import datetime
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='servercount', description='Get a number of servers the bot is in.')
@lightbulb.implements(lightbulb.SlashCommand)
async def server_count(ctx: lightbulb.SlashContext):
    await ctx.respond(
        embed=(
            hikari.Embed(
                title='Please wait!',
                description='We\'re asking around and getting the total count of all servers and how many members we have!\nThis wont take long.'
            )
        )
    )

    # A basic cache system to prevent spamming the API
    if ctx.bot.d['servercount_memory']['last_updated'] is not None:
        if ctx.bot.d['servercount_memory']['last_updated'] - datetime.datetime.now() < datetime.timedelta(hours=1):
            server_count = ctx.bot.d['servercount_memory']['count']
        else:
            my_guilds = await ctx.bot.rest.fetch_my_guilds()
            server_count = len(my_guilds)
            ctx.bot.d['servercount_memory']['last_updated'] = datetime.datetime.now()
            ctx.bot.d['servercount_memory']['count'] = server_count
    else:
        my_guilds = await ctx.bot.rest.fetch_my_guilds()
        server_count = len(my_guilds)
        ctx.bot.d['servercount_memory']['last_updated'] = datetime.datetime.now()
        ctx.bot.d['servercount_memory']['count'] = server_count

    member_count = get_member_total_count()

    if member_count < server_count:
        data = await count_all_servers_and_members()
        member_count = data['member_count']
        server_count = data['server_count']

    embed = (
        hikari.Embed(
            title="Server Count",
            description=f"I'm in {server_count} servers!"
        )
    )

    embed.add_field(
        name="Total Members",
        value=f"{member_count}",
    )

    await ctx.edit_last_response(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
