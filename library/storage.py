from datetime import datetime
import lightbulb
import logging
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
            'uid': 'INT',  # TODO: Just discovered this is a double-up of guild_id. Need to fix this
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
            'show_task_completion': 'BOOLEAN DEFAULT TRUE',
        },
        'user_contribution_log': {
            'contributed_task_uid': 'INT NOT NULL REFERENCES todo_items(uid)',
            'contributor_uuid': 'INT NOT NULL',
            'contribution_date': 'DATE DEFAULT CURRENT_TIMESTAMP',
            'task_for_guild_id': 'INT NOT NULL',
        },
        'guild_livelist_formats': {
            'guild_id': 'TEXT NOT NULL PRIMARY KEY',
            'text_format': 'TEXT'
        },
        'tasks_assigned_to_users': {
            'task_id': 'INT NOT NULL PRIMARY KEY',
            'user_id': 'INT NOT NULL',
        },
        'guild_livelist_descs': {
            'guild_id': 'INT NOT NULL PRIMARY KEY',
            'description': 'TEXT'
        }
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
    def set_livelist_description(desc, guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO guild_livelist_descs (guild_id, description) 
            VALUES (?, ?) 
            ON CONFLICT(guild_id) 
            DO UPDATE SET description = excluded.description
            """
            cur.execute(query, (guild_id, desc))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            # Lists name and function
            logging.error(f"An error occurred in {__name__} while trying to set the description for a guild's live list.", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_livelist_description(guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT description FROM guild_livelist_descs WHERE guild_id = ? LIMIT 1"
            cur.execute(query, (int(guild_id),))
            data = cur.fetchone()
            return data[0] if data is not None else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred Getting the show task completion", err)
            return None
        finally:
            conn.close()

    @staticmethod
    def get_task_incharge(task_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT user_id FROM tasks_assigned_to_users WHERE task_id = ? LIMIT 1"
            cur.execute(query, (int(task_id),))
            data = cur.fetchone()
            return data[0] if data is not None else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred Getting the show task completion", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def assign_user_to_task(user_id:int, task_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO tasks_assigned_to_users (user_id, task_id) VALUES (?, ?)
            """
            cur.execute(query, (user_id, task_id))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred while setting the assigned user for a task:", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def clear_task_incharge(task_id: int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            DELETE FROM tasks_assigned_to_users WHERE task_id = ?
            """
            cur.execute(query, (task_id,))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred while clearing the task in-charge:", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def save_livelist_format(guild_id, live_format):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO guild_livelist_formats (guild_id, text_format)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET text_format = excluded.text_format
            """
            cur.execute(query, (int(guild_id), live_format))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred while setting the live format:", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_livelist_format(guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT text_format FROM guild_livelist_formats WHERE guild_id = ? LIMIT 1"
            cur.execute(query, (int(guild_id),))
            data = cur.fetchone()
            return data[0] if data is not None else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred Getting the show task completion", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_show_task_completion(guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT show_task_completion FROM guild_settings WHERE uid = ? LIMIT 1"
            cur.execute(query, (int(guild_id),))
            data = cur.fetchone()
            return bool(data[0]) if data else False
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred Getting the show task completion", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def toggle_show_task_completion(status:bool, guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "UPDATE guild_settings SET show_task_completion = ? WHERE uid = ?"
            cur.execute(query, (status, int(guild_id),))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred trying to set a show task completion setting", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def set_new_task_data(task_id, task_name=None, task_desc=None, task_category=None):
        # Gets the task
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT name, description, category FROM todo_items WHERE id = ? LIMIT 1"
            cur.execute(query, (int(task_id),))
            old_name, old_description, old_category = cur.fetchone()
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred Getting a task from the list to update a task!", err)
            return False
        finally:
            conn.close()

        # Use old values if new ones are not provided
        if task_name is None:
            task_name = old_name
        if task_desc is None:
            task_desc = old_description
        if task_category is None:
            task_category = old_category

        # Update the task
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            UPDATE todo_items 
            SET name = ?, description = ?, category = ?
            WHERE id = ?
            """
            cur.execute(query, (task_name, task_desc, task_category, int(task_id)))
            conn.commit()  # Commit the changes to the database
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred editing a task in the list!", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_task_exists(task_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT 1 FROM todo_items WHERE id = ? LIMIT 1;"
            cur.execute(query, (int(task_id),))
            exists = cur.fetchone() is not None
            return exists
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error checking task existence: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def delete_task_from_list(task_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "DELETE FROM todo_items WHERE id = ?;"
            cur.execute(query, (int(task_id),))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occured deleting a task from the list!", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_is_task_completed(task_id:str):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT completed FROM todo_items WHERE id = ?"
            cur.execute(query, (task_id,))
            result = cur.fetchone()
            return False if not result else bool(result[0])
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error checking task completion: {err}")
            return err
        finally:
            conn.close()

    @staticmethod
    def get_livechannel_style(guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            SELECT style
            FROM livechannel_styles
            WHERE guild_id = ?
            """
            cur.execute(query, (guild_id,))
            data = cur.fetchone()
            return data[0] if data else "classic"
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting livechannel style for guild {guild_id}", err)
            return 'classic'
        finally:
            conn.close()


    @staticmethod
    def set_livechannel_style(style:str, guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            INSERT OR REPLACE INTO livechannel_styles (guild_id, style)
            VALUES (?, ?)
            """
            cur.execute(query, (guild_id, style))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Couldn't set live channel style for guild {guild_id}", err)
            return False
        finally:
            conn.close()

    # noinspection PyTypeChecker
    @staticmethod
    def get_category_exists(category: str) -> bool:
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            SELECT name
            FROM todo_items
            WHERE category = ?
            """
            cur.execute(query, (category,))
            data = cur.fetchone()
            return data is not None
        except sqlite3.Error as err:
            logging.error(f"An error occurred checking if the category exists: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_allow_late_contrib(guild_id: int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            SELECT allow_late_contrib
            FROM guild_settings
            WHERE uid = ?
            """
            cur.execute(query, (guild_id,))
            data = cur.fetchone()
            return bool(data[0]) if data else False
        except sqlite3.Error as err:
            logging.error(f"An error occurred retrieving late contribution setting: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def set_allow_late_contrib(guild_id: int, allow_late_contrib: bool):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            INSERT OR REPLACE INTO guild_settings (uid, allow_late_contrib)
            VALUES (?, ?)
            """
            cur.execute(query, (guild_id, allow_late_contrib))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred while setting late contribution: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def add_todo_item(name, description, user_id=None, guild_id=None, added_by: int = None, deadline: datetime = None, category=None):
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        try:
            assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
            assert type(name) is str and type(description) is str, "Name and description must be strings"
            assert type(added_by) is int or user_id is not None, "Added by must be an integer if user_id is None."
            assert added_by is not None if guild_id is not None else True, "Added by is needed if guild_id is provided."
            assert category is None or type(category) is str, "Category must be a string or None"
            cur = conn.cursor()

            uid = user_id if user_id else guild_id
            query = """
            INSERT INTO todo_items (uid, name, description, completed, added_by, deadline, guild_id, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cur.execute(query, (uid, name, description, False, added_by, deadline, guild_id, category))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred adding a to-do item: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def mark_todo_finished(identifier, user_id=None, guild_id=None):
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        try:
            assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
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
                    query += "AND name LIKE ?"
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
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred marking the task as finished: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def undo_mark_todo_finished(identifier, user_id=None, guild_id=None):
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        try:
            assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
            assert type(identifier) is str or type(identifier) is int, "Identifier must be a string or an integer"
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
                query += "AND name LIKE ?"
            arguments += (identifier,)

            cur.execute(query, arguments)
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred undoing the task completion: {err}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_todo_items(filter_for='*', guild_id=None, user_id=None, identifier=None):
        """
        Gets the to do items from the database.
        :param filter_for: The filter to apply to the to do items. Can be 'incompleted', 'completed', or '*'.
        :param guild_id: The guild ID to get the to do items for.
        :param user_id: The user ID to get the to do items for.
        :param identifier: The identifier to filter the to do items by. Can be the task ID or the task name.
        :return:
        """
        assert filter_for in ['incompleted', 'completed', '*'], "Filter must be either 'incompleted', 'completed' or *"
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        cur = conn.cursor()

        if guild_id is not None and user_id is not None:
            raise ValueError("Only provide either guild ID or User ID")
        else:
            if guild_id is None:
                assigned_guild_id = "*"
            else:
                assigned_guild_id = guild_id
            if user_id is None:
                assigned_user_id = "*"
            else:
                assigned_user_id = user_id

        uid = assigned_user_id if assigned_user_id else assigned_guild_id
        if guild_id is None and user_id is None:
            uid = "*"

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
            data = cur.fetchall()
        except sqlite3.OperationalError as err:
            logging.error("Failed to create a to-do list task.", err)
            return False
        finally:
            conn.close()

        # Filter out tasks that don't belong to the guild
        # Only filter by guild if a guild_id was actually provided
        if guild_id is not None:
            data = [task for task in data if task[7] == guild_id]


        return data  # Example data: [('Task 1', 'Description 1', False, 1, None, 123456789), ...]

    @staticmethod
    def set_taskchannel(guild_id, channel_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            INSERT OR REPLACE INTO guild_settings (uid, task_channel)
            VALUES (?, ?)
            """
            cur.execute(query, (guild_id, channel_id))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Couldn't set task channel for guild {guild_id}", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_taskchannel(guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            SELECT task_channel
            FROM guild_settings
            WHERE uid = ?
            """
            cur.execute(query, (guild_id,))
            data = cur.fetchone()

            return data[0] if data else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Couldn't get task channel for guild {guild_id}", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def clear_taskchannel(guild_id):
        """
        Clears the task channel for the guild. (Sets it to Null in the DB)
        :param guild_id: The guild ID to clear the task channel for.
        :return:
        """
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            UPDATE guild_settings
            SET task_channel = NULL
            WHERE uid = ?
            """
            cur.execute(query, (guild_id,))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error clearing task channel for {guild_id}", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def mark_user_as_contributing(user_id:int, task_id:int, guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            INSERT INTO user_contribution_log (contributed_task_uid, contributor_uuid, task_for_guild_id)
            VALUES (?, ?, ?)
            """
            cur.execute(query, (task_id, user_id, guild_id))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("Error marking user as contributing", err)
            return False
        finally:
            conn.close()


    @staticmethod
    def remove_contributor(user_id:int, task_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            DELETE FROM user_contribution_log
            WHERE contributed_task_uid = ? AND contributor_uuid = ?
            """
            cur.execute(query, (task_id, user_id))
            conn.commit()

            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error removing contributor for user {user_id}, task {task_id}", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_contributors(task_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()

            query = """
            SELECT contributor_uuid
            FROM user_contribution_log
            WHERE contributed_task_uid = ?
            """
            cur.execute(query, (task_id,))
            data = cur.fetchall()

            return [x[0] for x in data]  # Example output: [123456789, 987654321] (user IDs)
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting contributors for task {task_id}", err)
            return []
        finally:
            conn.close()

    @staticmethod
    def get_user_contributions(user_id:int, guild_id:int=-1):
        conn = sqlite3.connect(guild_filepath)
        try:
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
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting contributions from a user. user_id: {user_id}, guild: {guild_id}", err)
            return False
        finally:
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
        try:
            cur = conn.cursor()

            query = """
            SELECT guild_id
            FROM todo_items
            WHERE id = ?
            """
            cur.execute(query, (task_id,))
            data = cur.fetchone()
            return int(data[0]) if data else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error crossreferencing task ID {task_id}", err)
            return False
        finally:
            conn.close()



# noinspection PyNoneFunctionAssignment
class dataMan:
    """
    Essentially a class that processes data after it's been retrieved and ensures the data sent to the funcs is correct.
    """
    def __init__(self):
        self.storage = sqlite_storage

    def get_livelist_description(self, guild_id:int):
        guild_id = int(guild_id)
        return self.storage.get_livelist_description(guild_id)

    def set_livelist_description(self, desc:str|None, guild_id:int):
        guild_id = int(guild_id)
        if desc is not None:
            desc = str(desc)
        return self.storage.set_livelist_description(desc, guild_id)

    def get_task_incharge(self, task_id:int):
        task_id = int(task_id)
        return self.storage.get_task_incharge(task_id)

    def assign_user_to_task(self, user_id:int, task_id:int):
        user_id = int(user_id)
        if type(task_id) is not int and str(task_id).isnumeric() is False:
            raise TypeError("The task ID needs to be a number!")
        task_id = int(task_id)

        return self.storage.assign_user_to_task(user_id, task_id)

    def clear_task_incharge(self, task_id):
        task_id = int(task_id)
        return self.storage.clear_task_incharge(task_id)

    def get_livelist_format(self, guild_id:int):
        """
        :param guild_id:
        :return:
        """
        guild_id = int(guild_id)
        return self.storage.get_livelist_format(guild_id)

    def save_livelist_format(self, guild_id:int, live_format:str|None):
        """
        :param guild_id:
        :param live_format:
        :return:
        """
        guild_id = int(guild_id)
        return self.storage.save_livelist_format(guild_id=guild_id, live_format=live_format)

    def get_show_task_completion(self, guild_id:int):
        """
        :param guild_id:
        :return:
        """
        guild_id = int(guild_id)
        return self.storage.get_show_task_completion(guild_id)

    def toggle_show_task_completion(self, status:bool, guild_id:int):
        """
        :param status:
        :param guild_id:
        :return:
        """
        assert type(status) is bool
        guild_id = int(guild_id)

        return self.storage.toggle_show_task_completion(status, guild_id)

    def set_new_task_data(self, task_id, task_name=None, task_desc=None, task_category=None):
        """
        The task's old data will be rewritten with what is not None.
        :param task_id:
        :param task_name:
        :param task_desc:
        :param task_category:
        :return:
        """
        assert type(task_name) is str
        assert type(task_desc) is str
        return self.storage.set_new_task_data(
            task_id,
            task_name,
            task_desc,
            task_category
        )

    def get_task_exists(self, task_id):
        """
        Get if the task exists or not
        :return:
        """
        assert type(task_id) is int
        return self.storage.get_task_exists(task_id)

    def delete_task_from_list(self, task_id):
        """
        Delete a task so it no longer exists.
        :param task_id:
        :return:
        """
        assert type(task_id) is int
        if self.storage.get_task_exists(task_id) is False:
            return -1
        return self.storage.delete_task_from_list(task_id)

    def get_is_task_completed(self, task_id_or_name):
        """
        Gets if a task is completed or not
        :param task_id_or_name:
        :return:
        """
        task_id_or_name = str(task_id_or_name)
        return self.storage.get_is_task_completed(task_id_or_name)

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

        self.save_livelist_format(guild_id, None)

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
        """
        :param user_id:
        :param task_id:
        :param guild_id:
        :return: False if failed
        :return: True if Succeeded
        :return: -1 if already contributing
        :return: -2 if late contrib not allowed and tried to contrib
        """
        assert type(user_id) is int, "User ID must be an integer"
        assert type(task_id) is int, "Task ID must be an integer"

        # Ensure the user is not already contributing
        if user_id in self.get_contributors(task_id):
            return -1
        if self.get_is_task_completed(task_id) is True:
            if self.get_allow_late_contrib(guild_id) is False:
                return -2

        return self.storage.mark_user_as_contributing(user_id, task_id, guild_id=int(guild_id))

    def remove_contributor(self, user_id:int, task_id:int):
        assert type(user_id) is int, "User ID must be an integer"
        assert type(task_id) is int, "Task ID must be an integer"

        # Ensure the user is contributing
        if user_id not in self.get_contributors(task_id):
            return -1

        return self.storage.remove_contributor(user_id, task_id)

    def get_contributors(self, task_id:int) -> list[int]:
        assert type(task_id) is int, "Task ID must be an integer"

        # noinspection PyTypeChecker
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

    def mark_todo_not_finished(self, name_or_id, user_id=None, guild_id=None):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name_or_id) is str or type(name_or_id) is int, "Name must be a string or int"
        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.undo_mark_todo_finished(name_or_id, user_id=uid)
        else:
            return self.storage.undo_mark_todo_finished(name_or_id, guild_id=uid)

    def get_todo_items(self, filter_for='incompleted', user_id=None, guild_id=None, identifier=None, only_keys=[]):
        assert filter_for in ['incompleted', 'completed', '*'], "Filter must be either 'incompleted' or 'completed'"
        uid = int(user_id if user_id else guild_id) if user_id or guild_id else None
        if user_id:
            data = self.storage.get_todo_items(filter_for, user_id=uid, identifier=identifier)
        else:
            data = self.storage.get_todo_items(filter_for, guild_id=uid, identifier=identifier)

        if len(only_keys) > 0:
            acceptable_keys = ["name", "description", "completed", "id", "completed_on", "added_by", "deadline", "guild_id", "category"]
            for d_key in only_keys:
                if d_key not in acceptable_keys:
                    raise TypeError(f"This key type is not acceptable \"{d_key}\"")

            keys_crossref = {
                "name": 0,
                "description": 1,
                "completed": 2,
                "id": 3,
                "completed_on": 4,
                "added_by": 5,
                "deadline": 6,
                "guild_id": 7,
                "category": 8
            }
            dictionary = {}

            for task in data:
                task_id = str(task[3])
                if task_id not in dictionary:
                    dictionary[task_id] = {}

                for dict_Key in only_keys:
                    dictionary[task_id][dict_Key] = task[keys_crossref[dict_Key]]

            return dictionary
        else:
            return data

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

    # noinspection PyTypeChecker
    def get_taskchannel(self, guild_id:int) -> int|None :
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
