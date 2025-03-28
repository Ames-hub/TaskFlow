from library.live_task_channel import livetasks
from library.storage import dataMan
import lightbulb
import datetime
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(hikari.events.ReactionAddEvent)
async def on_reaction_add(event: hikari.ReactionAddEvent):
    # Only watch watched messages
    if event.message_id not in plugin.bot.d['watched_messages'].keys():
        return
    # Dont interact with self
    if event.user_id == plugin.bot.get_me().id:
        return

    if event.emoji_name == "✅":
        task_id = plugin.bot.d['watched_messages'][event.message_id][0]
        # Won't edit if it's been edited in the last couple seconds
        last_edited = plugin.bot.d['last_edited'][event.message_id]
        if datetime.datetime.now().timestamp() - last_edited.timestamp() < plugin.bot.d['reaction_cooldown']:
            return

        guild_id = plugin.bot.d['watched_messages'][event.message_id][1]
        # Checks if its already completed as a task (meaning they want to undo the completion)
        task_complete = dataMan().get_todo_items(filter_for='*', identifier=task_id, guild_id=guild_id)[0][2]
        if task_complete is True:
            return  # Allow other listener to handle

        # Edit the message to mark it as incomplete.
        plugin.bot.d['last_edited'][event.message_id] = datetime.datetime.now()
        message = await plugin.bot.rest.fetch_message(event.channel_id, event.message_id)

        task_name, task_desc, _, _, _, added_by, _, _, _ = dataMan().get_todo_items(guild_id=guild_id, identifier=task_id, filter_for='*')[0]

        completed_text = "Completed: ✅"
        task_desc = f"{task_desc}\n{completed_text}" if task_desc != "..." else completed_text
        task_desc += f"\nAdded by: <@{added_by}>"
        embed = (
            hikari.Embed(
                title="Found Tasks",
                description=None,
            )
            .add_field(
                name=f'{task_name}\n(ID: {task_id})',
                value=task_desc,
                inline=False
            )
            .set_footer(
                "React with ✅ to mark this task as completed/incomplete. Unreact to undo.\n"
                "React with 🔔 to indicate you intend to contribute to the completion of this task."
            )
        )
        dataMan().mark_todo_finished(task_id, guild_id=guild_id)
        await message.edit(embed)
        await livetasks.update(guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
