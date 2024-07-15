import lightbulb
import sqlite3
import os

plugin = lightbulb.Plugin(__name__)

DEBUG = os.environ.get("DEBUG", False)
key_seperator = "."
settings_path = "settings.json"
user_file = "data/users.sqlite"
guild_file = "data/guilds.sqlite"

os.makedirs("data", exist_ok=True)
# Create the sqlite file if it doesn't exist and create the tables
conn = sqlite3.connect(user_file)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS todo_items \
(id INTEGER PRIMARY KEY AUTOINCREMENT, uid INT, name TEXT, description TEXT, completed BOOLEAN)")

conn.commit()
conn.close()

conn = sqlite3.connect(guild_file)
cur = conn.cursor()

# UID is the guild ID and added_by is the user ID of the person who added the item.
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS todo_items 
    (id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid INT,
    name TEXT,
    description TEXT,
    completed BOOLEAN,
    completed_on DATE DEFAULT NULL,
    added_by INT NOT NULL)
    """)

cur.execute(
    """CREATE TABLE IF NOT EXISTS guild_settings
    (uid INT PRIMARY KEY, task_channel INT DEFAULT NULL)"""  # Task_channel will be either None or an Int.
)

conn.commit()
del conn, cur

class sqlite_storage:
    @staticmethod
    def add_todo_item(name, description, user_id=None, guild_id=None, added_by:int=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name) is str and type(description) is str, "Name and description must be strings"
        assert type(added_by) is int or user_id is not None, "Added by must be an integer if user_id is None."
        assert added_by is not None if guild_id is not None else True, "Added by is needed if guild_id is provided."
        conn = sqlite3.connect(user_file if user_id is not None else guild_file)
        cur = conn.cursor()

        uid = user_id if user_id else guild_id
        query = """
        INSERT INTO todo_items (uid, name, description, completed, added_by)
        VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(query, (uid, name, description, False, added_by))
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def mark_todo_finished(identifier, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        conn = sqlite3.connect(user_file if user_id is not None else guild_file)
        cur = conn.cursor()

        uid = user_id if user_id else guild_id
        query = """
        UPDATE todo_items
        SET completed = ?
        WHERE uid = ?
        """

        arguments = (True, uid)
        if identifier is not None:
            if str(identifier).isnumeric():
                query += "AND id = ?"
            else:
                query += "AND name LIKE ?"  # So people don't have to type the full name.
            arguments += (identifier,)

        cur.execute(query, arguments)

        # Sets the 'completed_on' date to the current moment.
        query = """
        UPDATE todo_items
        SET completed_on = CURRENT_TIMESTAMP
        WHERE uid = ?
        """
        cur.execute(query, (uid,))
        conn.commit()

        conn.close()

        return True

    @staticmethod
    def undo_mark_todo_finished(identifier, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(identifier) is str or type(identifier) is int, "Identifier must be a string or an integer"
        conn = sqlite3.connect(user_file if user_id is not None else guild_file)
        cur = conn.cursor()

        uid = user_id if user_id else guild_id
        query = """
        UPDATE todo_items
        SET completed = ?
        WHERE uid = ? 
        """
        arguments = (False, uid)
        if str(identifier).isnumeric():
            query += "AND id = ?"
        else:
            query += "AND name LIKE ?"  # So people don't have to type the full name.
        arguments += (identifier,)

        cur.execute(query, arguments)
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def get_todo_items(filter_for='*', guild_id=None, user_id=None, identifier=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert filter_for in ['incompleted', 'completed', '*'], "Filter must be either 'incompleted', 'completed' or *"
        conn = sqlite3.connect(user_file if user_id is not None else guild_file)
        cur = conn.cursor()

        uid = user_id if user_id else guild_id
        arguments = (uid,)
        query = """
        SELECT name, description, completed, id, completed_on, added_by
        FROM todo_items
        WHERE uid = ?
        """

        if filter_for.lower() != "*":  # excluding complete status filter when filter_for is '*'
            query += "AND completed = ?"
            if filter_for.lower() == "incompleted":
                arguments += (False,)
            else:
                arguments += (True,)

        if identifier is not None:
            if str(identifier).isnumeric():
                query += "AND id = ?"
                arguments += (identifier,)
            else:
                query += "AND name LIKE ? "
                arguments += (identifier,)

        cur.execute(query, arguments)
        data = cur.fetchall()
        conn.close()

        return data

    @staticmethod
    def set_taskchannel(guild_id, channel_id):
        conn = sqlite3.connect(guild_file)
        cur = conn.cursor()

        query = """
        INSERT OR REPLACE INTO guild_settings (uid, task_channel)
        VALUES (?, ?)
        """
        cur.execute(query, (guild_id, channel_id))
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def get_taskchannel(guild_id):
        conn = sqlite3.connect(guild_file)
        cur = conn.cursor()

        query = """
        SELECT task_channel
        FROM guild_settings
        WHERE uid = ?
        """
        cur.execute(query, (guild_id,))
        data = cur.fetchone()
        conn.close()

        return data[0] if data else None

    @staticmethod
    def clear_taskchannel(guild_id):
        """
        Clears the task channel for the guild. (Sets it to Null in the DB)
        :param guild_id: The guild ID to clear the task channel for.
        :return:
        """
        conn = sqlite3.connect(guild_file)
        cur = conn.cursor()

        query = """
        UPDATE guild_settings
        SET task_channel = NULL
        WHERE uid = ?
        """
        cur.execute(query, (guild_id,))
        conn.commit()
        conn.close()

        return True

class dataMan:
    def __init__(self):
        self.storage = sqlite_storage

    def add_todo_item(self, name, description, added_by:int, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name) is str and type(description) is str, "Name and description must be strings"
        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.add_todo_item(name, description, user_id=uid)
        else:
            return self.storage.add_todo_item(name, description, guild_id=uid, added_by=int(added_by))

    def mark_todo_finished(self, name_or_id, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name_or_id) is str or type(name_or_id) is int, "Name must be a string or int"
        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.mark_todo_finished(name_or_id, user_id=uid)
        else:
            return self.storage.mark_todo_finished(name_or_id, guild_id=uid)

    def undo_mark_todo_finished(self, name_or_id, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name_or_id) is str or type(name_or_id) is int, "Name must be a string or int"
        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.undo_mark_todo_finished(name_or_id, user_id=uid)
        else:
            return self.storage.undo_mark_todo_finished(name_or_id, guild_id=uid)

    def get_todo_items(self, filter_for='incompleted', user_id=None, guild_id=None, identifier=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert filter_for in ['incompleted', 'completed'], "Filter must be either 'incompleted' or 'completed'"
        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.get_todo_items(filter_for, user_id=uid, identifier=identifier)
        else:
            return self.storage.get_todo_items(filter_for, guild_id=uid, identifier=identifier)

    def set_taskchannel(self, guild_id:int, channel_id:int):
        """
        Guild only command. Sets the channel that has a live-list of tasks.
        :param guild_id: The guild ID where the task channel is.
        :param channel_id: The channel ID to set as the task channel.
        :return:
        """
        assert type(channel_id) is int, "Channel ID must be an integer"
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.set_taskchannel(guild_id, channel_id)

    def get_taskchannel(self, guild_id:int):
        """
        Guild only command. Gets the channel that has a live-list of tasks.
        :param guild_id: The guild ID where the task channel is.
        :return: The channel ID of the task channel.
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        channel_id = self.storage.get_taskchannel(guild_id)
        if channel_id is not None:
            return int(channel_id)
        else:
            return None

    def clear_taskchannel(self, guild_id:int):
        """
        Guild only command. Clears the task channel for the guild.
        :param guild_id: The guild ID to clear the task channel for.
        :return:
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.clear_taskchannel(guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
