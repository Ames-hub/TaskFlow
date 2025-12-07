import lightbulb
import hikari

plugin = lightbulb.Plugin(__name__)
@plugin.command
@lightbulb.app_command_permissions(dm_enabled=True)
@lightbulb.option(
    "page",
    "The help page you want to view.",
    type=hikari.OptionType.INTEGER,
    min_value=1,
    required=False,
    default=-1
)
# @lightbulb.add_cooldown (cooldown here)
@lightbulb.command(name='help', description="View basic data about the bot's usage!", pass_options=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def help_cmd(ctx: lightbulb.SlashContext, page: int):

    # Help page Index 
    if page == -1:
        embed = (
            hikari.Embed(
                title="Help Index",
                description="Here is a list of help pages you can view. Use `/help <page number>` to view a specific page.",
                colour=0x00FF00
            )
            .add_field(name="1. Overview", value="A general overview of the bot's usage and features, and some general advice.")
            .add_field(name="2. Custom Styling", value="Information about custom styling options for your tasks and lists.")
            .add_field(name="3. The live list", value="Information about the live list feature.")
            .add_field(name="4. Permissions", value="Information about the bot's permission system.")
            .add_field(name="5. Tasks", value="Information about managing tasks.")
        )
    # Help overview
    elif page == 1:
        embed = (
            hikari.Embed(
                title="Bot Usage",
                description="Hello! Thank you for choosing me for your server.",
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
                    "To set it up, please run **/livelist setchannel** And set a channel."
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
    elif page == 2:
        embed = (
            hikari.Embed(
                title="Custom Styling",
                description="Information about customization in various aspects of the bot.",
                colour=0x00FF00
            )
            .add_field(
                name="Fully Custom Live List",
                value="This bot has a fully customizable live list that you can change to suit your server's style!\n\n"
                "This can be customised by running 'livelist textstyle' with no options added, then clicking the button 'Set Custom Style'!\n" \
                "I recommend beforehand, you check out [this link by clicking on this text](https://gist.github.com/Ames-hub/d66e88c4780234682efc20eea62e94f0)"                
            )
            .add_field(
                name="Toggle X or Checkmark",
                value="You can also toggle whether or not you want the 'X' or 'Tick' To be visible on the live list!\n" \
                "Some said seeing a long list of 'x' made them feel guilty, so I added this option for them, and now you can use it too!\n\n"
                "This can be toggled by running 'livelist xtoggle'!"
            )
            .add_field(
                name="Changable description!",
                value="You can also change the description of the live list to suit your server's style!\n" \
                "This can be changed by running 'livelist setdesc'! Its not a very fancy feature, but its there if you want it!"
            )
        )
    elif page == 3:
        embed = (
            hikari.Embed(
                title="The live list",
                description="Information about the live list feature, TaskFlows primary feature!",
                colour=0x00FF00
            )
            .add_field(
                name="What is the live list?",
                value="The live list is a channel that you can set in your server that will always have an up-to-date list of your tasks!\n"
                "Whenever you add, remove, or complete a task, the live list will update to reflect those changes!"
            )
            .add_field(
                name="Set the channel",
                value="To set the live list channel, please run `/livelist setchannel` and choose a channel to set as the live list channel.\n"
                "We recommend a creating a new channel specifically for the live list, so it doesn't get lost in your other messages.\n"
                "If for some reason you are not getting updates, please make sure the bot has permission to send messages in the channel you set!"
            )
            .add_field(
                name="Customising the live list",
                value="The live list can be customized to suit your server's style!\n"
                "You can change the text style, toggle the X/Checkmark, and change the description of the live list!\n"
                "To do this, please run `/livelist textstyle`, `/livelist xtoggle`, and `/livelist setdesc` respectively.\n\n"
                "See page 2 of the help command for more information on custom styling!"
            )
            .add_field(
                name="When do updates happen?",
                value="The live list updates on the following events:\n"
                "1. A task is added\n"
                "2. A task is removed\n"
                "3. A task is marked as complete or incomplete\n"
                "4. Someone is marked as contributing or not contributing to a task\n"
                "5. The live list is manually updated using `/livelist update`"
            )
        )
    elif page == 4:
        embed = (
            hikari.Embed(
                title="Permissions",
                description="Information about the bot's permission system.",
                colour=0x00FF00
            )
            .add_field(
                name="Config Permissions",
                value="The bot has a permission system that allows you to control who can change the bot's settings.\n"
                "To set who can change the bot's settings, please run `/perms configperm` and set a specific permission.\n"
            )
            .add_field(
                name="Helper Role",
                value="The helper role is a role that allows users to interact with the tasks on your to-do list.\n"
                "To set the help role, please run `/perms helprole` and choose a role.\n"
                "If you leave this blank, anyone will be able to interact with the tasks on your to-do list.\n"
                "This is recommended if you want to allow everyone to manage tasks, "
                "but not so for big servers that may want to limit who can change interact with tasks."
            )
            .add_field(
                name="Why use permissions?",
                value="Using permissions allows you to control who can change the bot's settings and who can interact with the tasks.\n"
                "This is especially useful for bigger servers where you may not want everyone to be able to change the bot's settings or manage tasks.\n"
                "In essence however, taskflow was always designed for smaller groups that trust each other, so using permissions is optional, "
                "but still a good, working feature."
            )
        )
    elif page == 5:
        embed = (
            hikari.Embed(
                title="Tasks",
                description="Information about managing tasks with TaskFlow.",
                colour=0x00FF00
            )
            .add_field(
                name="Adding/Creating Tasks",
                value="To add a task, please run `/task create` and provide the options you wish to set."
            )
            .add_field(
                name="Managing Tasks",
                value="You can manage tasks by using commands such as `/task complete`, `/task delete`, `/task edit` and so on.\n"
            )
            .add_field(
                name="Contributors",
                value="You can set yourself as contributing to a task by using `/task contribute` or `/task uncontribute`.\n"
                "Contributors are those who work to get the task done."
            )
            .add_field(
                name="The In-Charge",
                value="The In-Charge is the person who is primarily responsible for the task.\n"
                "They have special permissions to control the task and its coordination.\n"
                "The in-charge can assign/remove contributors, message all contributors, and more.\n"
                "You can set the In-Charge of a task using `/incharge assign (task_id)`\n"
                "**NOTE: This feature is W.I.P And you will likely not see ALL these features.**"
            )
        )
    else:
        embed = (
            hikari.Embed(
                title="Help Error",
                description="The help page you requested does not exist. Please use `/help` to view the help index.",
                colour=0xFF0000
            )
        )

    await ctx.respond(embed, flags=hikari.MessageFlag.EPHEMERAL)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
