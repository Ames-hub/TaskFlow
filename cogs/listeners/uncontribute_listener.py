from library.live_task_channel import livetasks
from library.storage import dataMan
import lightbulb
import datetime
import hikari

plugin = lightbulb.Plugin(__name__)

@plugin.listener(hikari.events.ReactionDeleteEvent)
async def on_reaction_remove(event: hikari.ReactionDeleteEvent):
    # Only watch watched messages
    if event.message_id not in plugin.bot.d['watched_messages'].keys():
        return
    # Dont interact with self
    if event.user_id == plugin.bot.get_me().id:
        return

    if event.emoji_name == "🔔":
        task_id = plugin.bot.d['watched_messages'][event.message_id][0]
        # Won't edit if it's been edited in the last 5 seconds
        last_edited = plugin.bot.d['last_edited'][event.message_id]
        if datetime.datetime.now().timestamp() - last_edited.timestamp() < 5:
            return

        # Edit the message to mark it as incomplete.
        plugin.bot.d['last_edited'][event.message_id] = datetime.datetime.now()
        message = await plugin.bot.rest.fetch_message(event.channel_id, event.message_id)

        guild_id = plugin.bot.d['watched_messages'][event.message_id][1]
        try:
            task_name, task_desc, _, _, _, _ = dataMan().get_todo_items(
                filter_for='completed',
                identifier=task_id,
                guild_id=guild_id,
            )[0]
        except IndexError: # No tasks found
            dataMan().remove_contributor(user_id=int(event.user_id), task_id=int(task_id))
            await livetasks.update(guild_id)
            return

        completed_text = "Completed: ❌"
        task_desc = f"{task_desc}\n{completed_text}" if task_desc != "..." else completed_text
        embed = (
            hikari.Embed(
                title="Incompleted Tasks",
                description=None,
            )
            .add_field(
                name=f'{task_name}\n(ID: {task_id})',
                value=task_desc,
                inline=False
            )
            .set_footer(
                "React with ✅ to mark this task as completed. Unreact to undo.\n"
                "React with 🔔 to indicate you intend to contribute to the completion of this task."
            )
        )
        unmark_success = dataMan().remove_contributor(user_id=int(event.user_id), task_id=int(task_id))
        if not unmark_success:
            dm_channel = await event.app.rest.create_dm_channel(event.user_id)
            await dm_channel.send("You are already not contributing to this task.")
            return
        await message.edit(embed)
        await livetasks.update(guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
