from library.storage import set_member_count, get_member_count
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(hikari.events.MemberCreateEvent)
async def member_join_listener(event: hikari.events.MemberCreateEvent):
    guild_id = str(event.guild_id)
    if plugin.bot.d['member_counting'].get(guild_id, None) is None:
        member_count = get_member_count(int(event.guild_id))
        if member_count == 0:
            member_count = len(await plugin.bot.rest.fetch_members(event.guild_id))
            guild_id = int(event.guild_id)
            set_member_count(
                guild_id=guild_id,
                count=member_count,
            )
            plugin.bot.d[str(guild_id)]['member_counting'] = member_count
            return
        plugin.bot.d['member_counting'][guild_id] = member_count
    plugin.bot.d[guild_id]['member_counting'] += 1  # Update this as fast as possible in case of mass join events.

    guild_id = int(event.guild_id)
    set_member_count(
        guild_id=guild_id,
        count=plugin.bot.d['member_counting'],
    )

@plugin.listener(hikari.events.MemberDeleteEvent)
async def member_leave_listener(event: hikari.events.MemberDeleteEvent):
    guild_id = str(event.guild_id)
    if plugin.bot.d['member_counting'].get(guild_id, None) is None:
        member_count = get_member_count(int(event.guild_id))
        if member_count == 0:
            member_count = len(await plugin.bot.rest.fetch_members(event.guild_id))
            guild_id = int(event.guild_id)
            set_member_count(
                guild_id=guild_id,
                count=member_count,
            )
            plugin.bot.d[str(guild_id)]['member_counting'] = member_count
            return
        plugin.bot.d['member_counting'][guild_id] = member_count
    plugin.bot.d[guild_id]['member_counting'] -= 1  # Update this as fast as possible in case of mass join events.

    guild_id = int(event.guild_id)
    set_member_count(
        guild_id=guild_id,
        count=plugin.bot.d['member_counting'],
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
