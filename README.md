# TaskFlow
A Task management bot for Discord

## Features
- Create tasks with names, descriptions, deadlines, and categories
- Delete tasks
- Edit tasks
- Assign someone as an in-charge for a task
- Complete or undo completion of tasks
- Add deadlines to tasks (date and time)
- Mark/unmark self as a contributor to a task
- Toggleable live list of tasks
- Multiple styles for the live task list (five built-in styles)
- Custom live task list styling
- Highly configurable permissions for who can interact with tasks
- Permission management for servers of all sizes
- Bug reporting system to report issues with the bot
- A news command to stay up to date with what's happening with the bot!

## Self-hosting Installation
If you don't know how to do some steps in this installation guide, look up how to do it.<br>
You will need Python3.12.8 for this to work.

It is recommended you self-host as the internet for the provided bot is less than optimal,
but still quite usable.

1. Clone the repository to a folder on your computer
2. Open a terminal in the folder
3. Run `python3.12 -m venv venv` in the terminal to create a virtual environment
4. Run `./venv/scripts/activate` if your on windows, else run `source venv/bin/activate`<br>
This will activate the virtual environment
5. Run `pip install -r requirements.txt` in the terminal to install the required packages
6. Make sure you have a discord bot token, if you don't have one, create a new bot on the discord dev portal.
7. Run `python main.py` in the terminal to start the bot<br>
It will then take you through a rapid setup process.

### Secrets.env
The file accepts the following KWARGS
- TOKEN : str (Discord bot token)
- DEBUG : bool (Toggle on or off debug mode. Begins use of debug token)
- DEBUG_TOKEN: str (Another bot token for testing out of production)
- NEWS_SERVER_HOST: str (The [BulletMan News Server](https://github.com/Ames-hub/bulletman) host. Example input, 192.168.1.115:8000)
- PRIMARY_MAINTAINER_ID: int (The ID of whoever is in charge of the bots good condition)

## Usage
This bot makes use of Slash commands and discord buttons.<br>
To view a list of commands, go into discord and search through available commands.

To create a task, use /task create

To interact with a task and mark yourself as contributing to it or mark it as done,
Either use its according command, or /task view (a task id)

You can assign a task to someone specifically using the `/task assign` command.<br>
This makes them the designated in-charge for the task.

### Titles and IDs
Tasks have Titles (aka, names) and IDs. Names are sometimes unique, IDs are always unique.<br>
The name is what you assign to the task when you create it, the ID is assigned by the bot.<br>
If you want good results when searching for a task, use its ID. But the name works well too

When viewing a list of tasks, you can see the ID and name of each task.<br>
e.g.
```
Live Task List
This is a live list of incomplete and newly completed tasks.

Resist temptation to eat the cookie <- THIS IS THE TASK NAME / TITLE
(ID: 1)
Completed: ✅
Added by: @FriendlyFox.exe
```
This is not always how it looks, as there are customisable styles to how the live
task list looks. This is "Classic" Style.

### Interacting with a task
To view and interact with a task, you must select it by ID or name.<br>
Since if there are too many tasks in one result, we won't know which one you want to interact with.

To view a list of tasks, use `/tasks view` without any additional options.<br>

To view a specific task, use `/tasks view <task_id>` or `/tasks view <task_name>`<br>
However, if you're viewing by name, if there are two similarly named tasks, it will show both,
and we won't know which one you want to interact with.

### Live Task List
The live task list is a consistently auto-updated list of tasks that are incomplete and newly completed tasks.<br>
To enable the live task list, use `/live channel *<channel>`<br>
When setting a valid channel, a list of the status of all relevant tasks will be sent to that channel.<br>
A newly completed task is no longer considered newly completed after 7 days.

### Bug Reporting
If you encounter a bug or issue with the bot, you can use the `/bug_report` command to report it directly through the bot.
This will help the developers identify and fix the issue more quickly.

### "Seriously pls help" moments
If you find you're having a lot of trouble with the bot and the guide does not help enough,
please don't hesitate to ask for help.<br>
You can find me on discord @friendlyfox.exe
