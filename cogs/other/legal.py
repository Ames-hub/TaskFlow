import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='legal', description='View the ToS and Privacy Policy of the bot.')
@lightbulb.implements(lightbulb.SlashCommand)
async def legal(ctx: lightbulb.SlashContext):
    embed = (
        hikari.Embed(
            title="Legal",
            description="You can view the Terms of Serivce and Privacy Policy here.",
            colour=0x0000FF
        )
        .add_field(
            name="Terms of Service",
            value="[View Terms of Service](https://gist.github.com/Ames-hub/81af1250563da3b83f0b271133622a44)"
        )
        .add_field(
            name="Privacy Policy",
            value="[View Privacy Policy](https://gist.github.com/Ames-hub/7cbdd1bcd648c3ebc0f2ef25ff3f57fd)"
        )
    )
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
