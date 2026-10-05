import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(hikari.events.GuildJoinEvent)
async def guild_join_listener(event: hikari.events.GuildJoinEvent):
    if not event.guild.system_channel_id:
        return

    embed = (
        hikari.Embed(
            title="Taskflow Joined!",
            description="Thank you for inviting me to your server!"
        )
        .add_field(
            name="What am I?",
            value=(
                "I'm Taskflow, a bot developed by @friendlyfox.exe to help either individuals or teams coordinate their tasks on Discord. "
                "This bot has various tools built to assist for teams, and for individuals."
            )
        )
    )

    if plugin.bot.d['is_official'] is True:
        embed.add_field(
            name="Connection Problems",
            value=(
                "One thing to note while using this bot is connection issues, this bot is self-hosted in a country with not-so-great internet. "
                "This won't cause too many problems, but occassionally the bot won't respond in time before discord terminates it. "
                "So even if it DID do what you asked, it won't ALWAYS say so. This shouldn't happen to often, but it does definitely happen.\n\n"
                "To fix this issue, you can download the bot from 'https://github.com/Ames-hub/Taskflow' and run it yourself using a faster host. "
                "Regardless, if you just wanted to try out the bot or if you're ok with just re-running a command every once in a while, "
                "this is a good place to do that."
            )
        )

    await event.app.rest.create_message(
        event.guild.system_channel_id,
        embed
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
