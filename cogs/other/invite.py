import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.command(name='invite', description='Invite the bot to your server!')
@lightbulb.implements(lightbulb.SlashCommand)
async def invite(ctx: lightbulb.SlashContext):
    embed = (
        hikari.Embed(
            title="Thanks for picking us!",
            description="https://discord.com/oauth2/authorize?client_id=1262021444615933962",
            colour=0x00FF00
        )
    )
    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
