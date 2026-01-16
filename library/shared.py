import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)

def gen_incharge_assigned_embed(guild_name, task_name, task_id, assigner_id):
    guild_name = str(guild_name)
    task_name = str(task_name)
    task_id = int(task_id)
    assigner_id = int(assigner_id)
    embed = (
        hikari.Embed(
            title="Role assignment!",
            description=f"You have been assigned as the in-charge for the task '{task_name}' (Task ID {task_id}) by <@{assigner_id}>."
            f"\n\nThis happened in the server '{guild_name}'.",
            color=0x00FF00
        )
        .add_field(
            name="What's this mean?",
            value="Being in-charge means you are primarily responsible for this task. "
            "You will be able to control who's helping, and have access to all of the /incharge commands."
        )
    )
    return embed

def get_not_incharge_embed():
    return (
        hikari.Embed(
            title="Error",
            description="You are not the in-charge for this task.",
            color=0xFF0000
        )
    )

def get_no_incharge_embed():
    return (
        hikari.Embed(
            title="Error",
            description="No in-charge assigned for this task.",
            color=0xFF0000
        )
    )

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)