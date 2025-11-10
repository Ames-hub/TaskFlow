import lightbulb

plugin = lightbulb.Plugin("tferror")

class task_not_found(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id
        self.message = f"Task with ID {self.task_id} not found."
    def __str__(self):
        return self.message

class no_tasks(Exception):
    def __init__(self):
        self.message = "No tasks exist in this guild."
    def __str__(self):
        return self.message

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
