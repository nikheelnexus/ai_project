import sqlite3
import getpass
import os
import threading
from agent import common_agent

db_path = os.path.join(os.path.abspath(os.path.dirname(common_agent.__file__)), 'token_tracker.db')


class TokenTracker:
    def __init__(self, db_path=db_path):
        self.db_path = db_path
        self.thread_local = threading.local()
        self.create_tables()

    def get_connection(self):
        """Get a thread-specific database_old connection"""
        if not hasattr(self.thread_local, 'conn'):
            self.thread_local.conn = sqlite3.connect(self.db_path)
        return self.thread_local.conn

    def create_tables(self):
        # Create tables using a temporary connection
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,
                    user TEXT,
                    usertext TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS summary (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_input_tokens INTEGER DEFAULT 0,
                    total_output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                )
            ''')
            conn.execute('INSERT OR IGNORE INTO summary (id) VALUES (1)')
        conn.close()

    def add_transaction(self, transaction_id, input_tokens, output_tokens, total_tokens, usertext):
        user = getpass.getuser()
        conn = self.get_connection()  # Get thread-local connection
        with conn:
            conn.execute('''
                INSERT INTO transactions (transaction_id, input_tokens, output_tokens, total_tokens, user, usertext)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, input_tokens, output_tokens, total_tokens, user, usertext))

            conn.execute('''
                UPDATE summary
                SET total_input_tokens = total_input_tokens + ?,
                    total_output_tokens = total_output_tokens + ?,
                    total_tokens = total_tokens + ?
                WHERE id = 1
            ''', (input_tokens, output_tokens, total_tokens))

    def get_summary(self):
        conn = self.get_connection()  # Get thread-local connection
        cursor = conn.cursor()
        cursor.execute('SELECT total_input_tokens, total_output_tokens, total_tokens FROM summary WHERE id = 1')
        total_input, total_output, total = cursor.fetchone()

        cursor.execute('SELECT * FROM transactions')
        transactions = cursor.fetchall()

        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total,
            "transactions": [dict(zip([column[0] for column in cursor.description], row)) for row in transactions]
        }

    def stop_server(self):
        conn = self.get_connection()  # Get thread-local connection
        cursor = conn.cursor()
        cursor.execute('SELECT total_tokens FROM summary WHERE id = 1')
        total = cursor.fetchone()[0]
        return total < 1118800000000000