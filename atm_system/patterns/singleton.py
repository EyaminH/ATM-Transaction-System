"""
Singleton Pattern (Creational)
==============================
Problem it solves:
    Ensures that the database connection manager has only one instance
    throughout the application lifecycle, preventing multiple conflicting
    connections and resource leaks.

Alternative rejected:
    Global variable — a simple global variable holding the connection would
    work but offers no lazy initialization, no thread-safety guarantee, and
    pollutes the global namespace. The Singleton pattern encapsulates the
    instance management cleanly.
"""
import sqlite3
import threading
import os


class DatabaseManager:
    """
    Singleton database connection manager.

    Thread-safe implementation that ensures only one instance of the
    database manager exists. Uses a lock for thread safety.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path=None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path=None):
        if self._initialized:
            return
        self._db_path = db_path
        self._connection = None
        self._initialized = True

    @property
    def db_path(self):
        return self._db_path

    @db_path.setter
    def db_path(self, path):
        """Allow setting the db_path (used by tests with in-memory DB)."""
        self._db_path = path
        # Close existing connection if any
        if self._connection:
            self._connection.close()
            self._connection = None

    def get_connection(self):
        """Get database connection, creating one if it doesn't exist."""
        if self._connection is None:
            if self._db_path != ":memory:":
                os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            self._connection = sqlite3.connect(
                self._db_path, check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def execute(self, query, params=None):
        """Execute a query and return the cursor."""
        conn = self.get_connection()
        if params:
            return conn.execute(query, params)
        return conn.execute(query)

    def execute_many(self, query, params_list):
        """Execute a query with multiple parameter sets."""
        conn = self.get_connection()
        return conn.executemany(query, params_list)

    def commit(self):
        """Commit current transaction."""
        if self._connection:
            self._connection.commit()

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def init_db(self):
        """Initialize database tables."""
        conn = self.get_connection()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_number TEXT UNIQUE NOT NULL,
                pin_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                login_attempts INTEGER DEFAULT 0,
                locked_until TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                account_type TEXT DEFAULT 'savings',
                balance REAL DEFAULT 0.0,
                daily_withdrawn REAL DEFAULT 0.0,
                last_withdrawal_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_before REAL NOT NULL,
                balance_after REAL NOT NULL,
                target_account_id INTEGER,
                description TEXT,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (account_id) REFERENCES accounts(id),
                FOREIGN KEY (target_account_id) REFERENCES accounts(id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (used for testing)."""
        with cls._lock:
            if cls._instance and cls._instance._connection:
                cls._instance._connection.close()
            cls._instance = None
