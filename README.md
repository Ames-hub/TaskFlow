# TaskFlow
A Task management bot for discord

## Features
- Create tasks
- Complete or undo completion of tasks
- Toggleable live list of tasks

## Self-hosting Installation
If you don't know how to do some of the steps in this installation guide, look up how to do it.

1. Clone the repository to a folder on your computer
2. Open a terminal in the folder
3. Run `python3.11 -m venv venv` in the terminal to create a virtual environment
4. Run `./venv/scripts/activate` if your on windows, else run `source venv/bin/activate`<br>
This will activate the virtual environment
5. Run `pip install -r requirements.txt` in the terminal to install the required packages
6. Make sure you have a discord bot token, if you don't have one, create a new bot on the discord dev portal.
7. Run `python main.py` in the terminal to start the bot<br>
It will then take you through a very quick setup process.

## Usage
This bot runs entirely on slash commands and reaction events.<br>
Honestly, the bot is pretty self-explanatory, but just incase it's not, here's a quick guide.<br>
To see a list of commands, type but don't send `/` in a discord server with the bot
in it and then find the bot in the list. Discord will then show you a list of commands.

To create a task, use `/grouptasks create *<title> <description>`<br>
Name is required, description is optional.

### Titles and IDs
Tasks have Titles (aka, names) and IDs. Names are sometimes unique, IDs are always unique.<br>
The name is what you assign to the task when you create it, the ID is assigned by the bot.<br>

When viewing a list of tasks, you can see the ID and name of each task.<br>
eg,
```
Live Task List
This is a live list of incomplete and newly completed tasks.

Resist temptation to eat the cookie <- THIS IS THE TITLE
(ID: 1)
Completed: ✅
Added by: @FriendlyFox.exe
```

### Interacting with a task
To view and interact with a task, you must select it by ID or name.<br>
Since if there are too many tasks in 1 result, we won't know which one you want to interact with.

To view a list of tasks, use `/grouptasks view` without any additional options.<br>

To view a specific task, use `/grouptasks view <task_id>` or `/grouptasks view <task_name>`<br>
However, if you're viewing by name, if there's two similarly named tasks, it will show both,
and we won't know which one you want to interact with.

### Live Task List
The live task list is a consistently auto-updated list of tasks that are incomplete and newly completed tasks.<br>
To enable the live task list, use `/taskchannel *<channel>`<br>
When setting a valid channel, a list of the status of all relevant tasks will be sent to that channel.<br>
A newly completed task is no longer considered newly completed after 7 days.

### "Seriously pls help" moments
If you find you're having a lot of trouble with the bot and the guide does not help enough, please don't hesitate to ask for help.<br>
You can find me on discord @friendlyfox.exe
