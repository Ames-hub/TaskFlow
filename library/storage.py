from datetime import datetime
from library import tferror
import traceback
import lightbulb
import logging
import sqlite3
import hikari
import os
import re

plugin = lightbulb.Plugin(__name__)

DEBUG = os.environ.get("DEBUG", False)
user_file = "data/users.sqlite"
guild_filepath = "data/guilds.sqlite"

os.makedirs("data", exist_ok=True)

def get_traceback(bug_id):
    with sqlite3.connect(guild_filepath) as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT traceback, exc_type FROM bug_tracebacks WHERE ticket_id = ?
                """,
                (bug_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "traceback": str(row[0]).splitlines(),
                    "exc_type": str(row[1]),
                }
            else:
                return None
        except Exception as e:
            logging.error(f"Error while getting bug traceback: {e}", exc_info=e)
            return False

def save_traceback(ticket_id, exception):
    # unwrap Lightbulb cmd invocation error thing
    actual_exc = exception
    while hasattr(actual_exc, "__cause__") and actual_exc.__cause__:
        actual_exc = actual_exc.__cause__

    exc_type = type(actual_exc).__name__
    exc_traceback = traceback.format_exception(
        type(actual_exc), actual_exc, actual_exc.__traceback__
    )
    exc_traceback_str = "".join(exc_traceback)

    with sqlite3.connect(guild_filepath) as conn:
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO bug_tracebacks (ticket_id, traceback, exc_type)
                VALUES (?, ?, ?)
                """,
                (ticket_id, exc_traceback_str, exc_type)
            )
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error while saving traceback: {e}", exc_info=e)
            return False

def modernize_db():
    """
    This function is used to modernise the database to the current version. It will check if the tables exist, and
    if they don't, it will create them. If the tables do exist, it will check if the columns are up to date, and if
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
            'priority': 'INT DEFAULT 2',
        },
        'task_template_usage': {  # Used to know which tasks use which template
            'usage_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'template_id': 'INTEGER NOT NULL',
            'task_id': 'INTEGER NOT NULL',
        },
        'recurring_items': {  # The item of the recurring task itself
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'template_id': 'INT NOT NULL',
            'last_recur': 'DATE DEFAULT CURRENT_TIMESTAMP',
            'interval': 'INTEGER NOT NULL DEFAULT 1',
            'guild_id': 'INTEGER NOT NULL',
            'blame_id': 'INTEGER NOT NULL',
        },
        'recurring_tasks_instances': {  # The tasks created for recurring tasks by their items
            'task_id': 'INTEGER NOT NULL PRIMARY KEY',
            'recur_id': 'INTEGER NOT NULL',
        },
        'livechannel_styles': {  # Used to know which guild uses which style
            'guild_id': 'INTEGER PRIMARY KEY',
            'style': 'TEXT DEFAULT "classic"',
        },
        'guild_settings': {
            'uid': 'INTEGER PRIMARY KEY',
            'task_channel': 'INTEGER DEFAULT NULL',
            'allow_late_contrib': 'BOOLEAN DEFAULT FALSE',
            'show_task_completion': 'BOOLEAN DEFAULT TRUE',
        },
        'user_contribution_log': {  # Saves who is helping opposed to who is in charge
            'contributed_task_uid': 'INTEGER NOT NULL',
            'contributor_uuid': 'INTEGER NOT NULL',
            'contribution_date': 'DATE DEFAULT CURRENT_TIMESTAMP',
            'task_for_guild_id': 'INTEGER NOT NULL',
        },
        'guild_livelist_formats': {  # Saves the custom live list format
            'guild_id': 'TEXT NOT NULL PRIMARY KEY',
            'text_format': 'TEXT'
        },
        'tasks_assigned_to_users': {  # Saves the users assigned as an I/C to a task
            'task_id': 'INTEGER NOT NULL PRIMARY KEY',
            'user_id': 'INTEGER NOT NULL',
        },
        'guild_livelist_descs': {  # A Feature request that allows people to modify the description of the live list
            'guild_id': 'INTEGER NOT NULL PRIMARY KEY',
            'description': 'TEXT'
        },
        'guild_taskmaster_roles': {
            'guild_id': "INTEGER NOT NULL PRIMARY KEY",
            'role_id': "INT"
        },
        'guild_configperms': {  # Saves who can configure the bot per the guild permissions
            'guild_id': 'INTEGER NOT NULL PRIMARY KEY',
            'permission': 'TEXT DEFAULT NULL'
        },
        'task_templates': {
            'identifier': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'guild_id': 'INTEGER NOT NULL',
            'name': 'TEXT NOT NULL',
            'task_name': 'TEXT DEFAULT NULL',
            'task_desc': 'TEXT DEFAULT NULL',
            'task_category': 'TEXT DEFAULT NULL',
            'task_deadline': 'DATETIME DEFAULT NULL',
        },
        'bug_report_cases': {
            'ticket_id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'resolved': 'BOOLEAN DEFAULT FALSE',
            'reporter_id': 'INTEGER NOT NULL',
            'stated_bug': 'TEXT NOT NULL',
            'stated_reproduction': 'TEXT NOT NULL',
            'additional_info': 'TEXT',
            'problem_section': 'TEXT NOT NULL default "Not specified"',
            'received_date': "DATETIME DEFAULT (DATETIME('now', 'localtime'))",
            'resolved_date': 'DATETIME DEFAULT NULL',
            'severity': 'TEXT DEFAULT "medium"',
            'expected_result': 'TEXT DEFAULT NULL DEFAULT "Not specified"',
        },
        'bug_tracebacks': {
            'ticket_id': 'INTEGER NOT NULL REFERENCES bug_reports(bugid) PRIMARY KEY',
            'traceback': 'TEXT NOT NULL',  # Tracebacks for bugs that were auto-reported.
            'exc_type': 'TEXT NOT NULL'
        },
        'authbook': {
            'username': 'TEXT PRIMARY KEY',
            'password': 'TEXT NOT NULL',
            'arrested': 'BOOLEAN NOT NULL DEFAULT FALSE',
        },
        'user_sessions': {
            'username': 'TEXT',
            'token': 'TEXT NOT NULL PRIMARY KEY',
            'created_at': 'DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP',
            'expires_at': 'DATETIME NOT NULL',
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
                    try:
                        cur.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_properties};')
                    except sqlite3.OperationalError as err:
                        print(f"Error: {err} -- {table_name} -- {column_name} -- {column_properties}")
                        print(f"Error: {err} -- {columns_info}")
                        raise err

        # If the table doesn't exist, create it with columns
        else:
            columns_str = ', '.join(
                [f'{column_name} {column_properties}' for column_name, column_properties in columns.items()]
            )
            try:
                cur.execute(f'CREATE TABLE {table_name} ({columns_str});')
            except sqlite3.OperationalError as err:
                print(f"There was a problem creating the table {table_name} with columns {columns_str}")
                logging.error(f"An error occurred while creating the table {table_name} with columns {columns_str}", err)
                exit(1)

modernize_db()

def classify_severity(description: str) -> str:
    desc = description.lower()
    # Remove all symbols
    desc = re.sub(r"[^\w\s]", "", desc)

    severity_keywords = {
        "critical": ["crash", "died", "not responding", "no response", "freeze", "data loss", "cant use", "completely broken"],
        "high": ["doesnt work", "stops working", "fails", "error", "exception", "not functioning", "not working", "timeout"],
        "medium": ["slow", "lag", "delay", "inconsistent", "wrong output", "incorrect", "unexpected"],
        "low": ["typo", "formatting", "minor", "cosmetic", "alignment", "small bug"],
    }

    for severity, keywords in severity_keywords.items():
        for word in keywords:
            if word in desc:
                return severity

    # If no keywords matched, default to medium
    return "medium"

class sqlite_storage:
    @staticmethod
    def count_tasks(guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) FROM todo_items WHERE guild_id = ?
                """,
                (guild_id,)
            )
            data = cur.fetchone()
            return data[0]
        except sqlite3.Error as err:
            logging.error(f"An error occurred while counting tasks for guild {guild_id}: {err}", exc_info=err)
            return False
        finally:
            conn.close()

    @staticmethod
    def update_last_recur(recur_id, new_task_id):
        datenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE recurring_items
                SET last_recur = ?
                WHERE id = ?
                """,
                (datenow, recur_id)
            )

            cur.execute(
                """
                INSERT INTO recurring_tasks_instances (task_id, recur_id) 
                VALUES (?, ?)
                """,
                (new_task_id, recur_id)
            )

            conn.commit()
        except sqlite3.Error as err:
            logging.error(f"An error occurred while updating the last recur: {err}", exc_info=err)
            conn.rollback()
            return False
        finally:
            conn.close()
        return True

    @staticmethod
    def add_recurring_item(guild_id, interval, template_id, user_blame_id, get_recur_id=False):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO recurring_items (guild_id, interval, template_id, blame_id) VALUES (?, ?, ?, ?)",
                (guild_id, interval, template_id, user_blame_id)
            )
            conn.commit()
            if not get_recur_id:
                return True
            else:
                # returns the autoincremented "ID" in the recurring_items table
                return cur.lastrowid
        except sqlite3.Error as err:
            logging.error(f"An error occurred while inserting the task {template_id} into the database: {err}")
            conn.rollback()
            return False
        finally:
            cur.close()

    @staticmethod
    def get_recur_list(guild_id=None):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()
        if guild_id is None:
            cur.execute("SELECT id, template_id, last_recur, interval, guild_id, blame_id FROM recurring_items")
        else:
            cur.execute(
                """
                SELECT id, template_id, last_recur, interval, guild_id, blame_id
                FROM recurring_items WHERE guild_id = ?
                """,
                (guild_id,)
            )

        data = cur.fetchall()
        # Organize data
        organized_data = {}
        for row in data:
            organized_data[row[0]] = {
                'id': row[0],
                'template_id': row[1],
                'last_recur': row[2],
                'interval': row[3],
                'guild_id': row[4],
                'blame_id': row[5],
            }

        return organized_data

    @staticmethod
    def create_bug_report_ticket(reporter_id, stated_bug, stated_reproduction, problem_section, expected_result, additional_info=None, return_ticket=False):
        conn = sqlite3.connect(guild_filepath)

        severity = classify_severity(stated_bug)

        try:
            cur = conn.cursor()
            cur.execute(f'''
                INSERT INTO bug_report_cases (reporter_id, stated_bug, stated_reproduction, problem_section, expected_result, additional_info, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (int(reporter_id), stated_bug, stated_reproduction, problem_section, expected_result, additional_info, severity)
            )
            conn.commit()
            if return_ticket:
                return cur.lastrowid
            return True
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while creating a bug report ticket: {err}", err)
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def mark_bugreport_resolved(ticket_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(f'''
                UPDATE bug_report_cases SET resolved = TRUE WHERE ticket_id = ?
            ''', (ticket_id,))
            conn.commit()
            return True
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while trying to mark a bug report as resolved: {err}", err)
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def mark_bugreport_unresolved(ticket_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(f'''
                UPDATE bug_report_cases SET resolved = FALSE WHERE ticket_id = ?
            ''', (ticket_id,))
            conn.commit()
            return True
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while trying to mark a bug report as not resolved: {err}", err)
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def list_bug_reports(unresolved_only=True, ticket_id:int=None):
        query = """
            SELECT ticket_id, reporter_id, resolved, stated_bug, stated_reproduction, additional_info,
            received_date, resolved_date, severity, problem_section, expected_result
            FROM bug_report_cases
        """
        if unresolved_only:
            query += " WHERE resolved = FALSE"

        if ticket_id is not None:
            if unresolved_only is False:
                query += " WHERE ticket_id = ?"
            else:
                query += " AND ticket_id = ?"

        args = (ticket_id,) if ticket_id is not None else ()

        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(query, args)
            data = cur.fetchall()
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while trying to get the list of bug reports: {err}", err)
            return None
        finally:
            conn.close()

        parsed_data = []
        for row in data:
            parsed_data.append({
                'ticket_id': row[0],
                'reporter_id': row[1],
                'resolved': row[2],
                'stated_bug': row[3],
                'stated_reproduction': row[4],
                'additional_info': row[5],
                'received_date': row[6],
                'resolved_date': row[7],
                'severity': row[8],
                'problem_section': row[9],
                'expected_result': row[10],
            })

        return parsed_data

    @staticmethod
    def create_task_from_template(template_id, guild_id, task_creator_id:int, return_ticket=False):
        template_data = dataMan().get_task_template(template_id, guild_id)
        if template_data is False:
            return False
        if template_data is None:
            return None
        unique_template_id = template_data['id']
        task_name = template_data['task_name']
        task_desc = template_data['task_desc']
        task_cat = template_data['task_category']
        task_deadline = template_data['task_deadline']
        template_guild_id = template_data['guild_id']

        if guild_id != template_guild_id:
            return -1  # Wrong guild

        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            task_id = sqlite_storage.add_todo_item(
                name=task_name,
                description=task_desc,
                guild_id=guild_id,
                category=task_cat,
                deadline=task_deadline,
                added_by=int(task_creator_id),
                return_task_id=True
            )

            cur.execute(f'''
                INSERT INTO task_template_usage (task_id, template_id)
                VALUES (?, ?)''',
                (task_id, unique_template_id)
            )
            conn.commit()
            if return_ticket:
                return task_id
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred while creating a task from a template: {err}", err)
            return False
        finally:
            conn.close()

    # noinspection PyTypeChecker
    @staticmethod
    def create_task_template(template_name, task_name, task_desc, task_category, task_deadline, guild_id) -> dict:
        """
        Returns a dictionary with the task template data.

        Like {success: bool, template_id: int}

        :param guild_id:
        :param template_name: Name of the template.
        :param task_name: Name of the task.
        :param task_desc: Description of the task.
        :param task_category: Category of the task.
        :param task_deadline: Deadline of the task.
        :return:
        """
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(f'''
            INSERT INTO task_templates (name, task_name, task_desc, task_category, task_deadline, guild_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (template_name, task_name, task_desc, task_category, task_deadline, guild_id))
            template_id = cur.lastrowid
            conn.commit()
            return {'success': True, 'template_id': template_id}
        except sqlite3.OperationalError as e:
            logging.error(f"An error occurred while creating a task template: {e}")
            conn.rollback()
            return {'success': False, 'template_id': None}
        finally:
            conn.close()

    @staticmethod
    def get_task_template(template_id: int | str, guild_id:int):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            if template_id == "*":
                cur.execute('''
                    SELECT identifier, name, task_name, task_desc, task_category, task_deadline, guild_id
                    FROM task_templates
                    WHERE guild_id = ?''', (guild_id,)
                )
                data = cur.fetchall()

                parsed_dict = {}
                for data_item in data:
                    parsed_dict[data_item[0]] = {
                        'id': data_item[0],
                        'name': data_item[1],
                        'task_name': data_item[2],
                        'task_desc': data_item[3],
                        'task_category': data_item[4],
                        'task_deadline': data_item[5],
                        'guild_id': data_item[6]
                    }
                return parsed_dict

            if str(template_id).isdigit():
                cur.execute(
                    """
                    SELECT identifier, name, task_name, task_desc, task_category, task_deadline, guild_id
                    FROM task_templates WHERE identifier = ? AND guild_id = ?
                    """,
                    (template_id, guild_id,)
                )
            else:
                cur.execute(
                    """
                    SELECT identifier, name, task_name, task_desc, task_category, task_deadline, guild_id
                    FROM task_templates WHERE name LIKE ? AND guild_id = ?
                    """,
                    (f"%{template_id}%", guild_id)
                )
            data = cur.fetchone()
            if not data:
                return {}
            return {
                'id': data[0],
                'name': data[1],
                'task_name': data[2],
                'task_desc': data[3],
                'task_category': data[4],
                'task_deadline': data[5],
                'guild_id': data[6]
            }
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while getting the task templates: {err}", exc_info=True)
            conn.rollback()
            return False
        finally:
            conn.close()

    # noinspection PyTypeChecker
    @staticmethod
    def delete_task_template(identifier:int) -> bool:
        """
        Deletes task template and its child tasks, and usage references.
        """
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()
        try:
            cur.execute(f'''
                DELETE FROM task_templates WHERE identifier = ? -- Due to sensitivity, only allow task ID integer
            ''', (identifier,))
            conn.commit()
        except sqlite3.OperationalError as e:
            logging.error(f"An error occurred while creating a task template: {e}")
            conn.rollback()
            conn.close()
            return False

        try:
            cur.execute("""
                SELECT task_id FROM task_template_usage WHERE template_id = ?
                """,
                (identifier,)
            )
            data = cur.fetchall()
            task_id_list = [row[0] for row in data]
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while getting the task templates: {err}", exc_info=True)
            conn.rollback()
            return False

        try:
            cur.execute(f"""
                DELETE FROM todo_items WHERE id IN ({','.join(['?'] * len(task_id_list))})
                """,
                task_id_list
            )
            conn.commit()
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while deleting a task template: {err}", err)
            conn.rollback()
            conn.close()
            return False

        try:
            cur.execute(
                f"""
                DELETE FROM task_template_usage WHERE task_id IN ({','.join(['?'] * len(task_id_list))})
                """,
                task_id_list
            )
        except sqlite3.OperationalError as err:
            logging.error(f"An error occurred while deleting a task template: {err}", err)
            conn.rollback()
            conn.close()
        finally:
            conn.close()

        return True

    @staticmethod
    def set_guild_configperm(guild_id, permission):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO guild_configperms (guild_id, permission) 
            VALUES (?, ?) 
            ON CONFLICT(guild_id)
            DO UPDATE SET permission = excluded.permission
            """
            cur.execute(query, (guild_id, permission))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            # Lists name and function
            logging.error(f"An error occurred in {__name__} while trying to set the config perm for guild {guild_id}.", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_guild_configperm(guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT permission FROM guild_configperms WHERE guild_id = ? LIMIT 1"
            cur.execute(query, (int(guild_id),))
            data = cur.fetchone()
            return data[0] if data is not None else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred in {__name__} getting the config permisison for guild {guild_id}", err)
            return None
        finally:
            conn.close()

    @staticmethod
    def set_taskmaster_role(guild_id, role_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            INSERT INTO guild_taskmaster_roles (guild_id, role_id) 
            VALUES (?, ?) 
            ON CONFLICT(guild_id)
            DO UPDATE SET role_id = excluded.role_id
            """
            cur.execute(query, (guild_id, role_id))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            # Lists name and function
            logging.error(f"An error occurred in {__name__} while trying to set the taskmaster role for guild {guild_id}.", err)
            return False
        finally:
            conn.close()

    @staticmethod
    def get_taskmaster_role(guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT role_id FROM guild_taskmaster_roles WHERE guild_id = ? LIMIT 1"
            cur.execute(query, (int(guild_id),))
            data = cur.fetchone()
            return data[0] if data is not None else None
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred in {__name__} getting the taskmaster role for {guild_id}", err)
            return None
        finally:
            conn.close()

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
            logging.error("An error occurred getting the live list description", err)
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
            logging.error(f"An error occurred getting the task incharge for task {task_id}", err)
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
            ON CONFLICT(task_id) DO UPDATE SET user_id = excluded.user_id
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
    def set_new_task_data(task_id, task_name=None, task_desc=None, task_category=None, task_deadline=None):
        # Gets the task
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = "SELECT name, description, category, deadline FROM todo_items WHERE id = ? LIMIT 1"
            cur.execute(query, (int(task_id),))
            old_name, old_description, old_category, old_deadline = cur.fetchone()
        except sqlite3.Error as err:
            conn.rollback()
            logging.error("An error occurred Getting a task from the list to update a task!", err)
            return False
        except TypeError as err: # Does not exist
            raise tferror.task_not_found(task_id)
        finally:
            conn.close()

        # Use old values if new ones are not provided
        if not task_name:
            task_name = old_name
        if not task_desc:
            task_desc = old_description
        if not task_category:
            task_category = old_category
        if not task_deadline:
            task_deadline = old_deadline

        # Update the task
        conn = sqlite3.connect(guild_filepath)
        try:
            # noinspection PyUnresolvedReferences
            cur = conn.cursor()
            query = """
            UPDATE todo_items 
            SET name = ?, description = ?, category = ?, deadline = ?
            WHERE id = ?
            """
            cur.execute(query, (task_name, task_desc, task_category, task_deadline, int(task_id)))
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

    # noinspection PyUnreachableCode
    @staticmethod
    def add_todo_item(
            name,
            description,
            user_id=None,
            guild_id=None,
            added_by: int = None,
            deadline: datetime = None,
            category=None,
            return_task_id=False,
            priority:int=2
            ):
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        try:
            assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
            assert type(name) is str and type(description) is str, "Name and description must be strings"
            assert type(added_by) is int or user_id is not None, "Added by must be an integer if user_id is None."
            assert added_by is not None if guild_id is not None else True, "Added by is needed if guild_id is provided."
            assert category is None or type(category) is str, "Category must be a string or None"
            cur = conn.cursor()

            query = """
            INSERT INTO todo_items (name, description, completed, added_by, deadline, guild_id, category, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            cur.execute(query, (name, description, False, added_by, deadline, guild_id, category, priority))
            conn.commit()

            if return_task_id:
                task_id = cur.lastrowid
                return task_id

            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"An error occurred adding a to-do item: {err}", exc_info=err)
            return False
        finally:
            conn.close()

    @staticmethod
    def mark_todo_finished(identifier, user_id=None, guild_id=None):
        conn = sqlite3.connect(user_file if user_id is not None else guild_filepath)
        try:
            assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
            cur = conn.cursor()

            query = """
            UPDATE todo_items
            SET completed = ?
            WHERE guild_id = ?
            """

            arguments = (True, guild_id)
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
            WHERE guild_id = ?
            """
            cur.execute(query, (guild_id,))
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

            query = """
            UPDATE todo_items
            SET completed = ?
            WHERE guild_id = ? 
            """
            arguments = (False, guild_id)
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
        Gets the to-do items from the database.
        :param filter_for: The filter to apply to the to-do items. Can be 'incompleted', 'completed', or '*'.
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
        SELECT name, description, completed, id, completed_on, added_by, deadline, guild_id, category, priority
        FROM todo_items
        {"WHERE guild_id = ?" if uid != "*" else ""}
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
            logging.error("Failed to create a to-do list task.", exc_info=err)
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
            # noinspection PyInconsistentReturns
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

        # Organise the data into a dictionary
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

class error:
    class CannotFind(Exception):
        """
        A General "Cannot find" Error to indicate to systems that something cannot be found.
        """
        def __init__(self, message):
            self.message = message

        def __str__(self):
            return self.message

# noinspection PyNoneFunctionAssignment,PyTypeChecker
class dataMan:
    """
    Essentially, a class that processes data after it's been retrieved and ensures the data sent to the funcs is correct.
    Yes, this class is an excercise in futility because the actual function could just do it. But, welp. It has been like
    This since the start, so that's what we're doing!
    """
    def __init__(self):
        self.storage = sqlite_storage

    @staticmethod
    def list_recurring_items(guild_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            SELECT id, template_id, last_recur, interval, guild_id, blame_id FROM recurring_items WHERE guild_id = ?
            """
            cur.execute(query, (guild_id,))
            data = cur.fetchall()
            parsed_data = {}
            for item in data:
                parsed_data[item[0]] = {
                    "id": item[0],
                    "template_id": item[1],
                    "last_recur": item[2],
                    "interval": item[3],
                    "guild_id": item[4],
                    "blame_id": item[5]
                }
            return parsed_data
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting recurring items for guild {guild_id}", err)
            return []
        finally:
            conn.close()

    @staticmethod
    def get_recur_guild_id(recur_id):
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            query = """
            SELECT guild_id FROM recurring_items WHERE id = ?
            """
            cur.execute(query, (recur_id,))
            data = cur.fetchone()
            if data is not None:
                return data[0]
            else:
                raise error.CannotFind("Cannot find recurring item")
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting guild owns recurring task {recur_id}", err)
            return None
        finally:
            conn.close()

    @staticmethod
    def delete_recurring_task(identifier):
        conn = sqlite3.connect(guild_filepath)
        cur = conn.cursor()

        try:
            query = """
            SELECT recur_id FROM recurring_tasks_instances WHERE task_id = ?
            """
            cur.execute(query, (identifier,))
            data = cur.fetchone()
            if data is not None:
                recur_id = int(data[0])  # Extract from the tuple
            else:
                # Must assume that it's not a task ID and instead a recur ID.
                recur_id = identifier
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting data for deleting a recurring task where TASK ID is {identifier}", err)
            return False

        # Gets all the task IDs for instances of recur ID
        try:
            query = """
            SELECT task_id FROM recurring_tasks_instances WHERE recur_id = ?
            """
            cur.execute(query, (recur_id,))
            data = cur.fetchall()
            # Extracts from tuple into a list
            task_id_list = [data[0] for data in data]
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error getting data for deleting assosciated recur tasks with recur ID {recur_id}", err)
            return False

        # Delete from todo_items using the collected task IDs
        try:
            query = f"""
            DELETE FROM todo_items WHERE id IN ({','.join(['?'] * len(task_id_list))})
            """
            cur.execute(query, task_id_list)
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error deleting tasks with IDs {task_id_list} from todo_items for recur ID {recur_id}: {err}", err)

        try:
            query = """
            DELETE FROM recurring_tasks_instances WHERE recur_id = ? 
            """
            cur.execute(query, (recur_id,))
            conn.commit()
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error deleting recurring task instances by Recur ID where Recur ID is {recur_id}", err)
            # IF we can't do it, it's okay. It's not ABSOLUTELY necessary for us to do so

        try:
            query = """
            DELETE FROM recurring_items WHERE id = ?
            """
            cur.execute(query, (recur_id,))
            conn.commit()
            return True
        except sqlite3.Error as err:
            conn.rollback()
            logging.error(f"Error deleting recurring task item where Recur ID is {recur_id}", err)
            return False

    @staticmethod
    def get_recur_details_by_taskid(task_id):
        task_id = int(task_id)
        conn = sqlite3.connect(guild_filepath)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT recur_id FROM recurring_tasks_instances where task_id = ?
                """,
                (task_id,)
            )
            recur_id = cur.fetchone()
        except sqlite3.Error as err:
            logging.error(f"An error occurred while updating the last recur: {err}", exc_info=err)
            conn.rollback()
            return False

        try:
            recur_id = int(recur_id[0])
        except TypeError:
            # If it encounters a type error, the task does not exist.
            return False

        try:
            # Get the recurring item from the recur ID
            cur.execute(
                """
                SELECT id, template_id, last_recur, interval, guild_id, blame_id FROM recurring_items WHERE id = ?
                """,
                (recur_id,)
            )
            data = cur.fetchone()
            if data:
                return {
                    'id': data[0],
                    'template_id': data[1],
                    'task_id': data[2],
                    'interval': data[3],
                    'guild_id': data[4],
                    'blame_id': data[5],
                }
            else:
                return None
        except sqlite3.Error as err:
            logging.error(f"An error occurred while updating the last recur: {err}", exc_info=err)
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_last_recur(self, recur_id, task_id):
        recur_id = int(recur_id)
        task_id = int(task_id)
        return self.storage.update_last_recur(recur_id, task_id)

    def get_recur_list(self, guild_id:int=None):
        """
        Gets the recurring tasks from the database.
        :param guild_id: The guild ID to get the recurring tasks for.
        :return:
        """
        guild_id = int(guild_id) if guild_id else None
        return self.storage.get_recur_list(guild_id)

    def add_recurring_item(self, user_blame_id=int, guild_id:int=None, interval:int=1, template_id:int=None, get_recur_id:bool=False):
        """
        Adds a recurring item to the database.
        :return:
        """
        guild_id = int(guild_id)
        interval = int(interval)
        if str(template_id).isdigit():
            template_id = int(template_id)
        else:
            # Gets the template ID from the name
            raise NotImplementedError  # Todo: Make this function able to find ID from name
        return self.storage.add_recurring_item(guild_id, interval, template_id, user_blame_id, get_recur_id)

    def list_bug_reports(self, unresolved_only=False, ticket_id:int=None):
        unresolved_only = bool(unresolved_only)
        if ticket_id is not None:
            ticket_id = int(ticket_id)
        return self.storage.list_bug_reports(unresolved_only, ticket_id)

    def create_bug_report_ticket(self, reporter_id, stated_bug:str, stated_reproduction:str, problem_section: str, expected_result: str, additional_info:str=None, return_ticket=False):
        reporter_id = int(reporter_id)
        return self.storage.create_bug_report_ticket(
            reporter_id=reporter_id,
            return_ticket=return_ticket,
            stated_bug=stated_bug,
            stated_reproduction=stated_reproduction,
            additional_info=additional_info,
            problem_section=problem_section,
            expected_result=expected_result
        )

    def mark_bug_report_resolved(self, ticket_id):
        ticket_id = int(ticket_id)
        return self.storage.mark_bugreport_resolved(ticket_id)

    def mark_bug_report_unresolved(self, ticket_id):
        ticket_id = int(ticket_id)
        return self.storage.mark_bugreport_unresolved(ticket_id)

    def create_task_from_template(self, template_id:int, guild_id:int, task_creator_id:int, return_ticket=False):
        if str(template_id).isdigit():
            template_id = int(template_id)
        else:
            template_id = str(template_id)
        guild_id = int(guild_id)
        task_creator_id = int(task_creator_id)

        # Ensures the template exists
        template = self.storage.get_task_template(template_id, guild_id)
        if template is None:  # Template not found
            return None

        return self.storage.create_task_from_template(template_id, guild_id, task_creator_id, return_ticket)

    def create_task_template(self, template_name, task_name, task_desc, task_category, task_deadline:datetime|None, guild_id):
        """
        Creates a task template after validating the input data.
    
        :param guild_id:
        :param template_name: The name of the template
        :param task_name: The name of the task
        :param task_desc: The description of the task
        :param task_category: The category of the task
        :param task_deadline: The deadline of the task
        :return: Dictionary with success status and template ID
        """
        template_name = str(template_name).strip()
        if task_name is not None:
            task_name = str(task_name).strip()
        if task_desc is not None:
            task_desc = str(task_desc).strip()

        if not isinstance(task_deadline, datetime):
            raise ValueError(f"Task deadline must be a datetime object type if provided. Got {type(task_deadline)} ({task_deadline})")

        return self.storage.create_task_template(
            template_name=template_name,
            task_name=task_name,
            task_desc=task_desc,
            task_category=task_category,
            task_deadline=task_deadline,
            guild_id=guild_id
        )

    def get_task_template(self, identifier, guild_id:int) -> dict:
        if str(identifier).isnumeric():
            identifier = int(identifier)
        else:
            identifier = str(identifier).strip()

        if guild_id:
            guild_id = int(guild_id)

        return self.storage.get_task_template(identifier, guild_id)

    def delete_task_template(self, identifier):
        identifier = int(identifier)
        return self.storage.delete_task_template(identifier)

    def set_guild_configperm(self, guild_id, permission):
        """
        :param guild_id:
        :param permission: A string permission.
        :return:
        """
        guild_id = int(guild_id)
        if not type(permission) is str:
            raise ValueError(f"Permission not string! Got {type(permission)} ({permission})")

        permission_list = [
            'administrator',
            'manage server',
            'none',
            None
        ]

        if permission not in permission_list:
            raise ValueError(f"Invalid permission, outside of accepted list! {permission}")

        if permission == 'none':
            permission = None

        return self.storage.set_guild_configperm(guild_id, permission)

    def get_guild_configperm(self, guild_id:int, crossref:bool=True):
        guild_id = int(guild_id)
        data = self.storage.get_guild_configperm(guild_id)

        if crossref:
            perm_crossref = {
                'administrator': hikari.Permissions.ADMINISTRATOR,
                'manage server': hikari.Permissions.MANAGE_GUILD,
                'none': None
            }
            if data is not None:
                # noinspection PyTypeChecker
                return perm_crossref[data]
            else:
                return None
        else:
            return data

    def get_taskmaster_role(self, guild_id):
        guild_id = int(guild_id)
        return self.storage.get_taskmaster_role(guild_id)

    def set_taskmaster_role(self, guild_id, role_id):
        guild_id = int(guild_id)
        role_id = int(role_id)
        return self.storage.set_taskmaster_role(guild_id, role_id)

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

    def assign_user_to_task(self, user_id:int, task_id:int, guild_id):
        user_id = int(user_id)
        task_id = int(task_id)
        guild_id = int(guild_id)
        if type(task_id) is not int and str(task_id).isnumeric() is False:
            raise TypeError("The task ID needs to be a number!")

        if guild_id != self.crossref_task(task_id):
            return -1

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

    def set_new_task_data(self, task_id, task_name=None, task_desc=None, task_category=None, task_deadline:datetime|None=None):
        """
        The task's old data will be rewritten with what is not None.
        :param task_id:
        :param task_name:
        :param task_desc:
        :param task_category:
        :param task_deadline:
        :return:
        """
        assert type(task_name) is str
        assert type(task_desc) is str
        return self.storage.set_new_task_data(
            task_id,
            task_name,
            task_desc,
            task_category,
            task_deadline=task_deadline
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

        # As the new style is set (which is not custom), We remove the custom style (if it's set)
        # So the custom doesn't over-ride preset.
        self.save_livelist_format(guild_id, None)

        return self.storage.set_livechannel_style(style, guild_id)

    def get_category_exists(self, category_name) -> bool:
        """
        Checks if a category exists.
        :param category_name:
        :return: Bool
        """
        assert type(category_name) is str, "Category name must be a string"
        return self.storage.get_category_exists(category_name)

    def crossref_task(self, task_id:int):
        """
        Gets the guild ID for a task.
        :param task_id: The task ID to get the guild ID for.
        :return: The guild ID for the task.
        """
        task_id = int(task_id)
        return self.storage.crossref_task(task_id)

    def get_allow_late_contrib(self, guild_id:int):
        """
        Guild-only command. Gets the setting for allowing late contributions.
        :param guild_id: The guild ID to get the setting for.
        :return: The setting for allowing late contributions.
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.get_allow_late_contrib(guild_id)

    def set_allow_late_contrib(self, guild_id:int, allow_late_contrib:bool):
        """
        Guild-only command. Sets the setting for allowing late contributions.
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
        :return: False if it failed,
        :return: True if it Succeeded
        :return: -1 if already contributing
        :return: -2 if late contrib is not allowed and tried to contrib
        :return: -3 in a different server as the task
        """
        assert type(user_id) is int, "User ID must be an integer"
        assert type(task_id) is int, "Task ID must be an integer"

        # Ensure the user is not already contributing
        if user_id in self.get_contributors(task_id):
            return -1
        if self.get_is_task_completed(task_id) is True:
            if self.get_allow_late_contrib(guild_id) is False:
                return -2

        if guild_id != self.crossref_task(task_id):
            return -3

        return self.storage.mark_user_as_contributing(user_id, task_id, guild_id=int(guild_id))

    def remove_contributor(self, user_id:int, task_id:int, guild_id:int):
        assert type(user_id) is int, "User ID must be an integer"
        assert type(task_id) is int, "Task ID must be an integer"

        # Ensure the user is contributing
        if user_id not in self.get_contributors(task_id):
            return -1

        if guild_id != self.crossref_task(task_id):
            return -2

        return self.storage.remove_contributor(user_id, task_id)

    def get_contributors(self, task_id:int) -> list[int]:
        assert type(task_id) is int, "Task ID must be an integer"

        # noinspection PyTypeChecker
        return self.storage.get_contributors(task_id)

    def add_todo_item(
            self,
            name,
            description,
            added_by:int,
            user_id=None,
            guild_id=None,
            deadline:datetime=None,
            category=None,
            return_task_id:bool=False,
            priority:int=2
            ):
        assert user_id is not None or guild_id is not None, "You must provide either a user_id or a guild_id"
        assert type(name) is str and type(description) is str, "Name and description must be strings"

        if priority > 5:
            raise ValueError("Priority must be less than 5")
        if priority < 0:
            raise ValueError("Priority must be greater than 0")

        uid = int(user_id if user_id else guild_id)
        if user_id:
            return self.storage.add_todo_item(
                name,
                description,
                user_id=uid,
                deadline=deadline,
                added_by=int(added_by),
                category=category,
                priority=priority,
            )
        else:
            return self.storage.add_todo_item(
                name,
                description,
                guild_id=uid,
                added_by=int(added_by),
                deadline=deadline,
                category=category,
                return_task_id=return_task_id,
                priority=priority,
            )

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

    def get_todo_items(self, filter_for='incompleted', user_id=None, guild_id=None, identifier=None, only_keys=None):
        if only_keys is None:
            only_keys = []
        assert filter_for in ['incompleted', 'completed', '*'], "Filter must be either 'incompleted' or 'completed'"
        uid = int(user_id if user_id else guild_id) if user_id or guild_id else None
        if user_id:
            data = self.storage.get_todo_items(filter_for, user_id=uid, identifier=identifier)
        else:
            data = self.storage.get_todo_items(filter_for, guild_id=uid, identifier=identifier)

        if len(only_keys) > 0:
            acceptable_keys = ["name", "description", "completed", "id", "completed_on", "added_by", "deadline", "guild_id", "category", "priority"]
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
                "category": 8,
                "priority": 9,
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
            parsed_data = {}
            for task in data:
                parsed_data[task[3]] = {
                    "name": task[0],
                    "description": task[1],
                    "completed": bool(task[2]),
                    "uid": task[3],
                    "completed_on": task[4],
                    "added_by": task[5],
                    "deadline": task[6],
                    "guild_id": task[7],
                    "category": task[8],
                    "priority": task[9],
                }
            return parsed_data

    def set_taskchannel(self, guild_id:int, channel_id:int):
        """
        Guild-only command. Sets the channel that has a live-list of tasks.
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
        Guild-only command. Gets the channel that has a live-list of tasks.
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
        Guild-only command. Clears the task channel for the guild.
        :param guild_id: The guild ID to clear the task channel for.
        :return:
        """
        assert type(guild_id) is int, "Guild ID must be an integer"
        return self.storage.clear_taskchannel(guild_id)

def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)
def unload(bot):
    bot.remove_plugin(plugin)
