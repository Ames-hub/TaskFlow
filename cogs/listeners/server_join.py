import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(hikari.events.GuildJoinEvent)
async def server_join_listener(event: hikari.events.GuildJoinEvent):
    embed = (
        hikari.Embed(
            title="Bot Usage",
            description="Hello! Thank you for adding me to your server. If you wish to learn how to use me, please read the rest of this message!",
            colour=0x0000FF
        )
        .add_field(
            name="What is TaskFlow?",
            value="Taskflow is a to-do list bot for discord that is intended to allow coordination between groups,"
                  "or to simply be a to-do list for someone.\n\n"
        )
        .add_field(
            name="! Live List !",
            value="The primary unique feature of TaskFlow is the live list.\n"
                  "This list shows you a list that is up-to-date with every change you make to your tasks.\n\n"
                  "To set it up, please run **/live channel** And set a channel."
        )
        .add_field(
            name="Permissions",
            value="Taskflow has a basic permissions system that allows you to change who can do what.\n\n"
                  "There is `/perms configperm` which allows you to configure who can change the bot's settings.\n"
                  "And there is `/perms helprole` which allows you to set who can interact with the tasks on your to-do list!\n\n"
                  "You may leave this blank if you want anyone to be able to interact with the tasks and change the bot."
        )
        .add_field(
            name="Bug reports",
            value="Bug reports are extremely helpful to me as they allow me to solve problems I wouldn't be able to find on my own.\n"
                  "If you see a bug or anything weird, please report it using /bug_report."
        )
        .add_field(
            name="That's it!",
            value="If you have any questions, feel free to join the support server or DM the creator @friendlyfox.exe!\n"
        )
    )

    sys_chan_id = event.guild.system_channel_id
    if sys_chan_id is None:
        sys_chan = await event.guild.fetch_system_channel()
        await sys_chan.send(embed=embed)
    else:
        await event.app.rest.create_message(
            channel=sys_chan_id,
            embed=embed
        )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
