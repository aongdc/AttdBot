"""
Class defined for Database and functions to access and modify the database.
"""
import sqlite3
import datetime


class Database:
    def __init__(self, db_path, setup=False):
        self.db_path = db_path
        if setup:
            self.setup()

    def create_connection(self):
        """
        Create a database connection to the SQLite database,
        as specified by db_file.

        :param db_file: str, path to database file
        :return: Connection object or None
        """
        self.conn = None
        try:
            self.conn = sqlite3.Connection(self.db_path)
        except Exception as e:
            print(e)

        return self.conn

    def setup(self):
        self.conn = self.create_connection()
        self.conn.cursor().execute("CREATE TABLE IF NOT EXISTS users ("
                                   "time_registered TEXT,"
                                   "name INTEGER,"
                                   "user_id INTEGER NOT NULL,"
                                   "first_name TEXT,"
                                   "user_name TEXT,"
                                   "is_admin INTEGER NOT NULL DEFAULT 0,"
                                   "is_deleted INTEGER NOT NULL DEFAULT 0)")
        self.conn.commit()

    def get_users_table(self, active_only=True):
        cmd = "SELECT * FROM users"
        if active_only:
            cmd += "  WHERE is_deleted=0"
        self.cur = self.create_connection().cursor().execute(cmd)

        return self.cur

    def get_user_id_lst(self):
        # user_id is 3rd column
        self.user_id_lst = [x[2] for x in self.get_users_table()]

        return self.user_id_lst

    def get_user_id_map(self):
        # maps name to corresponding user_id
        # name is 2nd column, user_id is 3rd column
        self.user_id_map = dict()
        tuple_map = [x[1:3] for x in self.get_users_table()]
        for name, id in tuple_map:
            self.user_id_map[id] = name

        return self.user_id_map

    def add_user(self, name, user_id, first_name, user_name, time_registered=None, set_as_admin=0, set_as_deleted=0):
        self.conn = self.create_connection()
        if not time_registered:
            time_registered = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')

        cur_users_table = self.get_users_table(active_only=False).fetchall()
        cmd = f"INSERT INTO users (time_registered, name, user_id, first_name, user_name, is_admin, is_deleted) " \
              f"VALUES ('{time_registered}', '{name}', '{user_id}', '{first_name}', '{user_name}', '{set_as_admin}', '{set_as_deleted}')"

        for user in cur_users_table:
            _, user, id, _, _, is_admin, is_deleted = user
            if id == user_id and user == name:
                cmd = f"UPDATE users SET time_registered='{time_registered}', is_deleted=0 WHERE user_id='{id}' AND name='{user}"
                break

        self.cur = self.conn.cursor().execute(cmd)
        self.conn.commit()

        return self.cur

    def user_info(self, user_id, active_only=True):
        cmd = f"SELECT * FROM users WHERE user_id='{user_id}'"
        if active_only:
            cmd += ' AND is_deleted=0'
        self.cur = self.create_connection().cursor().execute(cmd)

        cols = ["time_reg", "name", "user_id", "first_name", "user_name", "is_admin", "is_deleted"]
        user_info_dict = dict(zip(cols, self.cur.fetchall()[0]))

        return user_info_dict

    def register_as_admin(self, user_id):
        self.conn = self.create_connection()
        self.cur = self.conn.cursor().execute(f"UPDATE users SET is_admin=1 WHERE user_id='{user_id}'")
        self.conn.commit()

        return True

    def deactivate_user(self, user_id):
        self.conn = self.create_connection()
        self.cur = self.conn.cursor().execute(f"UPDATE users SET is_deleted=1 WHERE user_id='{user_id}'")
        self.conn.commit()

        return True


if __name__ == '__main__':
    from envs import DATABASE_PATH

    # lst = Database(DATABASE_PATH).get_user_id_lst()
    conn = Database(DATABASE_PATH).create_connection()
    conn.commit()
