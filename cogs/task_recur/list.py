from cogs.task_recur.group import group
from library.storage import dataMan
import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

@group.child
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command(name='list', description='List all of the recurring tasks for your server', pass_options=True)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def command(ctx: lightbulb.SlashContext):
    dm = dataMan()
    recur_list = dm.list_recurring_items(ctx.guild_id)

    embed_desc = ""
    for item_id in recur_list:
        item = recur_list[item_id]
        embed_desc += (
            f"Recur ID {item['id']}\n"
            f"Last Recur (y/m/d): {item['last_recur']}\n"
            f"Recur Interval: Every {item['interval']} Day(s)\n"
            f"Recur Creator: <@{item['blame_id']}>\n\n"
        )

    embed = (
        hikari.Embed(
            title='Recurring Task List',
            description=embed_desc,
        )
    )

    await ctx.respond(embed)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
