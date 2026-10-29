"""
Module 2: Account Management Service
======================================
Handles account creation, balance inquiry, account details, and
linking accounts to users.
"""
import random
import string


class AccountService:
    """Manages bank accounts linked to ATM users."""

    def __init__(self, db_manager):
        self.db = db_manager

    @staticmethod
    def generate_account_number():
        """Generate a unique 10-digit account number."""
        return "".join(random.choices(string.digits, k=10))

    def create_account(self, user_id, account_type="savings", initial_balance=0.0):
        """Create a new bank account for a user."""
        # Generate unique account number
        account_number = self.generate_account_number()
        while self.get_account_by_number(account_number):
            account_number = self.generate_account_number()

        self.db.execute(
            """INSERT INTO accounts (user_id, account_number, account_type, balance)
               VALUES (?, ?, ?, ?)""",
            (user_id, account_number, account_type, initial_balance),
        )
        self.db.commit()

        account = self.get_account_by_number(account_number)
        return account

    def get_account_by_number(self, account_number):
        """Retrieve an account by its account number."""
        row = self.db.execute(
            "SELECT * FROM accounts WHERE account_number = ?",
            (account_number,),
        ).fetchone()
        return dict(row) if row else None

    def get_account_by_id(self, account_id):
        """Retrieve an account by its ID."""
        row = self.db.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_accounts_by_user(self, user_id):
        """Get all accounts belonging to a user."""
        rows = self.db.execute(
            "SELECT * FROM accounts WHERE user_id = ? AND is_active = 1",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_balance(self, account_id):
        """Get the current balance of an account."""
        account = self.get_account_by_id(account_id)
        if account:
            return account["balance"]
        return None

    def get_all_accounts(self):
        """Get all accounts in the system (admin use)."""
        rows = self.db.execute(
            """SELECT a.*, u.full_name, u.card_number
               FROM accounts a
               JOIN users u ON a.user_id = u.id
               ORDER BY a.created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

    def deactivate_account(self, account_id):
        """Deactivate an account (admin action)."""
        self.db.execute(
            "UPDATE accounts SET is_active = 0, updated_at = datetime('now') WHERE id = ?",
            (account_id,),
        )
        self.db.commit()
        return True

    def activate_account(self, account_id):
        """Activate an account (admin action)."""
        self.db.execute(
            "UPDATE accounts SET is_active = 1, updated_at = datetime('now') WHERE id = ?",
            (account_id,),
        )
        self.db.commit()
        return True
