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

    if event.emoji_name == "🔔":
        guild_id = int(plugin.bot.d['watched_messages'][event.message_id][1])
        task_id = plugin.bot.d['watched_messages'][event.message_id][0]
        # Won't edit if it's been edited in the last 5 seconds
        last_edited = plugin.bot.d['last_edited'][event.message_id]
        if datetime.datetime.now().timestamp() - last_edited.timestamp() < 5:
            return

        # Edit the message to mark it as incomplete.
        plugin.bot.d['last_edited'][event.message_id] = datetime.datetime.now()
        message = await plugin.bot.rest.fetch_message(event.channel_id, event.message_id)

        try:
            task_name, task_desc, is_completed, _, _, added_by, _, _ = dataMan().get_todo_items(
                guild_id=guild_id,
                identifier=task_id,
                filter_for='*'
            )[0]
        except IndexError:
            # No tasks found. Therefore, no tasks to contribute to.
            # If the code managed to get this far, that's a bug.
            return

        # Checks if the task is already completed.
        if bool(dataMan().get_allow_late_contrib(guild_id)) is False:
            if is_completed:
                dm_channel = await event.app.rest.create_dm_channel(event.user_id)
                await dm_channel.send("This task is already completed and cannot be contributed to any longer.")
                return

        completed_text = "Completed: ✅ " if is_completed else "Completed: ❌"
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
        mark_success = dataMan().mark_user_as_contributing(
            user_id=int(event.user_id),
            task_id=int(task_id),
            guild_id=guild_id
        )

        dm_channel = await event.app.rest.create_dm_channel(event.user_id)
        if not mark_success:
            await dm_channel.send("You have already indicated that you intend to contribute to this task.")
            return
        else:
            await dm_channel.send("You are now contributing to that task.")

        await message.edit(embed)
        await livetasks.update(guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
