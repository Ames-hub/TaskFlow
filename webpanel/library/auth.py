from library.storage import guild_filepath as DB_PATH
from fastapi import HTTPException
from fastapi import Request
import datetime
import sqlite3
import secrets
import logging

def require_valid_token(request: Request):
    token = request.cookies.get("sessionKey") or request.headers.get("Authorization")

    redirect = False
    if not token:
        redirect = True
    elif not authbook.verify_token(token):
        redirect = True

    if redirect:
        raise HTTPException(status_code=401, detail="Invalid token")

    return token

class autherrors:
    class InvalidPassword(Exception):
        def __init__(self, password):
            self.password = password

        def __str__(self):
            return f"Password \"{self.password}\" is invalid for that account."

    class UserNotFound(Exception):
        def __init__(self, username):
            self.username = username

        def __str__(self):
            return f"User \"{self.username}\" Not found."

    class ExistingUser(Exception):
        def __init__(self, username):
            self.username = username

        def __str__(self):
            return f"User \"{self.username}\" already exists."

    class AccountArrested(Exception):
        def __init__(self, username):
            self.username = username
        def __str__(self):
            return f"User \"{self.username}\"'s account has been arrested."

class authbook:
    @staticmethod
    def token_owner(token):
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(f"SELECT username FROM user_sessions WHERE token = ?", (token,))
            row = cur.fetchone()
            if row is None:
                raise autherrors.UserNotFound("Unknown")
            return row[0]
        finally:
            conn.close()

    @staticmethod
    def create_account(username, password):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO authbook (username, password) VALUES (?, ?)
                    """,
                    (username, password,),
                )
                conn.commit()
                logging.info(f"Account under the name {username} created")
                return True
        except sqlite3.IntegrityError:
            logging.info(f"Someone tried to make the account {username}, but it already existed.")
            raise autherrors.ExistingUser(username)
        except sqlite3.Error as err:
            logging.error("Error connecting to database!", exc_info=err)
            conn.rollback()
            return False

    @staticmethod
    def check_password(username, password):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT password FROM authbook WHERE username = ?
                    """,
                    (username,),
                )
                try:
                    fetched_pass = cur.fetchone()[0]
                except TypeError:
                    raise autherrors.UserNotFound(username)

                if password == fetched_pass:
                    return True
                else:
                    return False
        except sqlite3.Error as err:
            logging.error("Error connecting to database!", exc_info=err)
            return False

    @staticmethod
    def verify_token(token):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT token FROM user_sessions WHERE token = ?
                    """,
                    (token,),
                )
                try:
                    data = cur.fetchone()[0]
                except TypeError:
                    return False

                return data == token
        except sqlite3.Error as err:
            logging.error("Error connecting to database!", exc_info=err)
            return False

    @staticmethod
    def check_arrested(username):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT arrested FROM authbook WHERE username = ?
                    """,
                    (username,),
                )
                try:
                    data = cur.fetchone()[0]
                except TypeError:
                    raise autherrors.UserNotFound(username)
                return data
        except sqlite3.Error as err:
            logging.error("Error connecting to database and running command!", exc_info=err)
            conn.rollback()
            return True  # IF we can't check it, assume everyone's arrested.

def get_token_owner(token):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT username FROM user_sessions
            WHERE token = ?
            AND expires_at > DATE('now')
            ORDER BY created_at DESC
            """,
            (token,)
        )
        data = cur.fetchone()
        conn.close()
        if data:
            return data[0]
        else:
            return None
    except sqlite3.Error as err:
        logging.error("Error connecting to database!", exc_info=err)
        conn.close()
        return None

# noinspection PyMethodMayBeStatic
class UserLogin:
    def __init__(self, details: dict):
        if details.get("token", None) is None:
            self.username = details["username"]
            self.password = details["password"]
            self.token = None
        else:
            self.username = get_token_owner(token=details["token"])
            self.password = None
            self.token = details["token"]

        if self.token is not None:
            valid = authbook.check_password(self.username, self.password)
            if not valid:
                raise autherrors.InvalidPassword(self.password)

        self.arrested = authbook.check_arrested(self.username)
        if self.arrested is True:
            raise autherrors.AccountArrested(self.username)

        self.store_token(self.gen_token())

    def store_token(self, token):
        expires_at = datetime.datetime.now() + datetime.timedelta(hours=2)  # expires in 2 hours
        logging.info("New token generated.")

        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO user_sessions (username, token, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (self.username, token, datetime.datetime.now(), expires_at),
            )
            conn.commit()
            return True
        except sqlite3.Error as err:
            logging.error("Failed to store login token", exc_info=err)
            conn.rollback()
            return False
        finally:
            conn.close()

    def gen_token(self):
        token = f"{secrets.token_hex(8)}-{secrets.token_hex(4)}.KNOWLEDGE.{secrets.token_hex(4)}-{secrets.token_hex(8)}"
        return token