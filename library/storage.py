from datetime import datetime
import lightbulb
import sqlite3
import os

plugin = lightbulb.Plugin(__name__)

DEBUG = os.environ.get("DEBUG", False)
key_seperator = "."
settings_path = "settings.json"
user_file = "data/users.sqlite"
guild_filepath = "data/guilds.sqlite"

os.makedirs("data", exist_ok=True)

def modernize_db():
    """
    This function is used to modernize the database to the current version. It will check if the tables exist and
    if they don't, it will create them. If the tables do exist, it will check if the columns are up to date and if
    they aren't, it will update them.

    :return:
    """
    # Function I pulled from another project.
    # Using this dict, it formats the SQL query to create the tables if they don't exist
    table_dict = {
        'todo_items': {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'uid': 'INT',
            'name': 'TEXT',
            'description': 'TEXT',
            'completed': 'BOOLEAN',
            'completed_on': 'DATE DEFAULT NULL',
            'added_by': 'INT NOT NULL',
            'deadline': 'DATETIME DEFAULT NULL',
            'guild_id': 'INT DEFAULT NULL',
            'category': 'TEXT DEFAULT NULL',
        },
        'livechannel_styles': {
            'guild_id': 'INT PRIMARY KEY',
            'style': 'TEXT DEFAULT "classic"',
        },
        'guild_settings': {
            'uid': 'INT PRIMARY KEY',
            'task_channel': 'INT DEFAULT NULL',
            'allow_late_contrib': 'BOOLEAN DEFAULT FALSE',
        },
        'user_contribution_log': {
            'contributed_task_uid': 'INT NOT NULL REFERENCES todo_items(uid)',
            'contributor_uuid': 'INT NOT NULL',
            'contribution_date': 'DATE DEFAULT CURRENT_TIMESTAMP',
            'task_for_guild_id': 'INT NOT NULL',
        },
    }

    for table_name, columns in table_dict.items():
        with sqlite3.connect(guild_filepath) as conn:
            cur = conn.cursor()
            cur.execute(f'''
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name='{table_name}';
                ''')
            table_exist = cur.fetchone() is not None

        # If the table exists, check and update columns
        if table_exist:
            for column_name, column_properties in columns.items():
                # Check if the column exists
                cur.execute(f'''
                        PRAGMA table_info({table_name});
                    ''')
                columns_info = cur.fetchall()
                column_exist = any(column_info[1] == column_name for column_info in columns_info)

                # If the column doesn't exist, add it
                if not column_exist:
                    cur.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_properties};')

        # If the table doesn't exist, create it with columns
        else:
            columns_str = ', '.join(
                [f'{column_name} {column_properties}' for column_name, column_properties in columns.items()]
            )
            try:
                cur.execute(f'CREATE TABLE {table_name} ({columns_str});')
            except sqlite3.OperationalError:
                exit(1)

modernize_db()

class sqlite_storage:
    @staticmethod
    def get_livechannel_style(guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        SELECT style
        FROM livechannel_styles
        WHERE guild_id = ?
        """
        cur.execute(query, (guild_id,))
        data = cur.fetchone()
        conn.close()

        return data[0] if data else "classic"

    @staticmethod
    def set_livechannel_style(style:str, guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        INSERT OR REPLACE INTO livechannel_styles (guild_id, style)
        VALUES (?, ?)
        """
        cur.execute(query, (guild_id, style))
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def get_category_exists(category:str):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        SELECT name
        FROM todo_items
        WHERE category = ?
        """
        cur.execute(query, (category,))
        data = cur.fetchone()
        conn.close()

        return data is not None

    @staticmethod
    def get_allow_late_contrib(guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        SELECT allow_late_contrib
        FROM guild_settings
        WHERE uid = ?
        """
        cur.execute(query, (guild_id,))
        data = cur.fetchone()
        conn.close()

        return data[0] if data else False

    @staticmethod
    def set_allow_late_contrib(guild_id:int, allow_late_contrib:bool):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        INSERT OR REPLACE INTO guild_settings (uid, allow_late_contrib)
        VALUES (?, ?)
        """
        cur.execute(query, (guild_id, allow_late_contrib))
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def add_todo_item(name, description, user_id=None, guild_id=None, added_by:int=None, deadline:datetime=None, category=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name) is str and type(description) is str, "Name and description must be strings"
        assert type(added_by) is int or user_id is not None, "Added by must be an integer if user_id is None."
        assert added_by is not None if guild_id is not None else True, "Added by is needed if guild_id is provided."
        assert category is None or type(category) is str, "Category must be a string or None"
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        cur = conn.cursor()

        uid = user_id if user_id else guild_id
        query = """
        INSERT INTO todo_items (uid, name, description, completed, added_by, deadline, guild_id, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cur.execute(query, (uid, name, description, False, added_by, deadline, guild_id, category))
        conn.commit()

        conn.close()

        return True

    @staticmethod
    def mark_todo_finished(identifier, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
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
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
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
        """
        Gets the todo items from the database.
        :param filter_for: The filter to apply to the todo items. Can be 'incompleted', 'completed', or '*'.
        :param guild_id: The guild ID to get the todo items for.
        :param user_id: The user ID to get the todo items for.
        :param identifier: The identifier to filter the todo items by. Can be the task ID or the task name.
        :return:
        """
        assert filter_for in ['incompleted', 'completed', '*'], "Filter must be either 'incompleted', 'completed' or *"
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        cur = conn.cursor()

        if guild_id is None:
            guild_id = "*"
        if user_id is None:
            user_id = "*"

        uid = user_id if user_id else guild_id
        arguments = (uid,) if uid != "*" else ()
        query = f"""
        SELECT name, description, completed, id, completed_on, added_by, deadline, guild_id, category
        FROM todo_items
        {"WHERE uid = ?" if uid != "*" else ""}
        """

        WHERE_OR_AND_TEXT = "and" if uid != "*" else "where"

        if filter_for.lower() != "*":  # excluding complete status filter when filter_for is '*'
            query += f"{WHERE_OR_AND_TEXT} completed = ?"
            WHERE_OR_AND_TEXT = "and"
            if filter_for.lower() == "incompleted":
                arguments += (False,)
            else:
                arguments += (True,)

        if identifier is not None:
            if str(identifier).isnumeric():
                query += f"{WHERE_OR_AND_TEXT} id = ?"
                arguments += (identifier,)
            else:
                query += f"{WHERE_OR_AND_TEXT} name LIKE ? "
                arguments += (identifier,)

        try:
            cur.execute(query, arguments)
        except sqlite3.OperationalError as e:
            print(e)
            print(query, arguments)
            raise e
        data = cur.fetchall()
        conn.close()

        # Filter out tasks that don't belong to the guild
        if guild_id is not None:
            data = [task for task in data if task[7] == guild_id]

        return data  # Example data: [('Task 1', 'Description 1', False, 1, None, 123456789), ...]

    @staticmethod
    def set_taskchannel(guild_id, channel_id):
        conn = sqlite3.connect(guild_filepath)
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
        conn = sqlite3.connect(guild_filepath)
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
        conn = sqlite3.connect(guild_filepath)
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

    @staticmethod
    def mark_user_as_contributing(user_id:int, task_id:int, guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        INSERT INTO user_contribution_log (contributed_task_uid, contributor_uuid, task_for_guild_id)
        VALUES (?, ?, ?)
        """
        cur.execute(query, (task_id, user_id, guild_id))
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def remove_contributor(user_id:int, task_id:int):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        DELETE FROM user_contribution_log
        WHERE contributed_task_uid = ? AND contributor_uuid = ?
        """
        cur.execute(query, (task_id, user_id))
        conn.commit()
        conn.close()

        return True

    @staticmethod
    def get_contributors(task_id:int):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        SELECT contributor_uuid
        FROM user_contribution_log
        WHERE contributed_task_uid = ?
        """
        cur.execute(query, (task_id,))
        data = cur.fetchall()
        conn.close()

        return [x[0] for x in data]  # Example output: [123456789, 987654321] (user IDs)

    @staticmethod
    def get_user_contributions(user_id:int, guild_id:int=-1):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = f"""
        SELECT contributed_task_uid
        FROM user_contribution_log
        WHERE contributor_uuid = ?
        {'AND task_for_guild_id = ?' if guild_id != -1 else ''}
        """
        cur.execute(query, (user_id, guild_id) if guild_id != -1 else (user_id,))
        data = cur.fetchall()

        task_ids = [x[0] for x in data]  # Example output: [1, 2, 3] (task IDs)

        # get all the data for the tasks
        query = """
        SELECT name, description, completed, id, completed_on, added_by
        FROM todo_items
        WHERE id = ?
        """
        task_data = []
        for task_id in task_ids:
            cur.execute(query, (task_id,))
            task_data.append(cur.fetchone())

        conn.close()

        # Organize the data into a dictionary
        data = {}
        for task in task_data:
            data[task[3]] = {
                "name": task[0],
                "description": task[1],
                "completed": task[2],
                "uid": task[3],
                "completed_on": task[4],
                "added_by": task[5]
            }

        return data

    @staticmethod
    def crossref_task(task_id):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        query = """
        SELECT guild_id
        FROM todo_items
        WHERE task_id = ?
        """
        cur.execute(query, (task_id,))
        data = cur.fetchone()
        conn.close()

        return data[0] if data else None

class dataMan:
    def __init__(self):
        self.storage = sqlite_storage

    def get_livechannel_style(self, guild_id:int):
        """
        Gets the style for the live channel.
        :param guild_id: The guild ID to get the style for.
        :return: The style for the live channel.
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.get_livechannel_style(guild_id)

    def set_livechannel_style(self, style:str, guild_id:int):
        """
        Sets the style for the live channel.
        :param style: The style to set.
        :param guild_id: The guild ID to set the style for.
        :return:
        """
        assert type(style) is str, "Style must be a string"
        assert style.lower() in ['classic', 'minimal', 'pinned', 'compact', 'pinned-minimal'], "Style must be valid"
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.set_livechannel_style(style, guild_id)

    def get_category_exists(self, category_name) -> bool:
        """
        Checks if a category exists.
        :param category_name:
        :return: bool
        """
        assert type(category_name) is str, "Category name must be a string"
        return self.storage.get_category_exists(category_name)

    def crossref_task(self, task_id:int):
        """
        Gets the guild ID for a task.
        :param task_id: The task ID to get the guild ID for.
        :return: The guild ID for the task.
        """
        assert type(task_id) is int, "Task ID must be an integer"
        return self.storage.crossref_task(task_id)

    def get_allow_late_contrib(self, guild_id:int):
        """
        Guild only command. Gets the setting for allowing late contributions.
        :param guild_id: The guild ID to get the setting for.
        :return: The setting for allowing late contributions.
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.get_allow_late_contrib(guild_id)

    def set_allow_late_contrib(self, guild_id:int, allow_late_contrib:bool):
        """
        Guild only command. Sets the setting for allowing late contributions.
        :param guild_id: The guild ID to set the setting for.
        :param allow_late_contrib: The setting for allowing late contributions.
        :return:
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        assert type(allow_late_contrib) is bool, "Allow late contrib must be a boolean"
        return self.storage.set_allow_late_contrib(guild_id, allow_late_contrib)

    def get_user_contributions(self, user_id:int, guild_id:int=-1):
        assert type(user_id) is int, "User ID must be an integer"
        assert type(guild_id) is int, "Guild ID must be an integer"

        return self.storage.get_user_contributions(user_id, guild_id)

    def mark_user_as_contributing(self, user_id:int, task_id:int, guild_id:int):
        assert type(user_id) is int, "User ID must be an integer"
        assert type(task_id) is int, "Task ID must be an integer"

        # Ensure the user is not already contributing
        if user_id in self.get_contributors(task_id):
            return False

        return self.storage.mark_user_as_contributing(user_id, task_id, guild_id=int(guild_id))

    def remove_contributor(self, user_id:int, task_id:int):
        assert type(user_id) is int, "User ID must be an integer"
        assert type(task_id) is int, "Task ID must be an integer"

        # Ensure the user is contributing
        if user_id not in self.get_contributors(task_id):
            return False

        return self.storage.remove_contributor(user_id, task_id)

    def get_contributors(self, task_id:int) -> list[int]:
        assert type(task_id) is int, "Task ID must be an integer"

        return self.storage.get_contributors(task_id)

    def add_todo_item(self, name, description, added_by:int, user_id=None, guild_id=None, deadline:datetime=None, category=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name) is str and type(description) is str, "Name and description must be strings"
        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.add_todo_item(name, description, user_id=uid, deadline=deadline, added_by=int(added_by), category=category)
        else:
            return self.storage.add_todo_item(name, description, guild_id=uid, added_by=int(added_by), deadline=deadline, category=category)

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
        assert filter_for in ['incompleted', 'completed', '*'], "Filter must be either 'incompleted' or 'completed'"
        uid = int(user_id if user_id else guild_id) if user_id or guild_id else None
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
