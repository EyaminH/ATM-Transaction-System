"""
Module 5: Admin Service
========================
Provides administrative functions: view all accounts, user management,
system monitoring, and audit log viewing.
"""


class AdminService:
    """Administrative operations for the ATM system."""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_system_stats(self):
        """Get overall system statistics."""
        total_users = self.db.execute(
            "SELECT COUNT(*) as count FROM users"
        ).fetchone()["count"]

        active_users = self.db.execute(
            "SELECT COUNT(*) as count FROM users WHERE is_active = 1"
        ).fetchone()["count"]

        total_accounts = self.db.execute(
            "SELECT COUNT(*) as count FROM accounts"
        ).fetchone()["count"]

        total_balance = self.db.execute(
            "SELECT COALESCE(SUM(balance), 0) as total FROM accounts WHERE is_active = 1"
        ).fetchone()["total"]

        total_transactions = self.db.execute(
            "SELECT COUNT(*) as count FROM transactions"
        ).fetchone()["count"]

        today_transactions = self.db.execute(
            "SELECT COUNT(*) as count FROM transactions WHERE date(created_at) = date('now')"
        ).fetchone()["count"]

        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_accounts": total_accounts,
            "total_balance": total_balance,
            "total_transactions": total_transactions,
            "today_transactions": today_transactions,
        }

    def get_all_users(self):
        """Get a list of all users in the system."""
        rows = self.db.execute(
            """SELECT id, card_number, full_name, email, phone,
                      is_admin, is_active, login_attempts, created_at
               FROM users
               ORDER BY created_at DESC"""
        ).fetchall()
        return [dict(r) for r in rows]

    def toggle_user_status(self, user_id):
        """Activate or deactivate a user."""
        user = self.db.execute(
            "SELECT is_active FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return False, "User not found."

        new_status = 0 if user["is_active"] else 1
        self.db.execute(
            "UPDATE users SET is_active = ?, updated_at = datetime('now') WHERE id = ?",
            (new_status, user_id),
        )
        self.db.commit()
        action = "activated" if new_status else "deactivated"
        return True, f"User {action} successfully."

    def unlock_user(self, user_id):
        """Unlock a user's account (reset login attempts)."""
        self.db.execute(
            """UPDATE users
               SET login_attempts = 0, locked_until = NULL,
                   updated_at = datetime('now')
               WHERE id = ?""",
            (user_id,),
        )
        self.db.commit()
        return True, "User account unlocked."

    def get_audit_log(self, limit=50):
        """Retrieve recent audit log entries."""
        rows = self.db.execute(
            """SELECT al.*, u.full_name, u.card_number
               FROM audit_log al
               LEFT JOIN users u ON al.user_id = u.id
               ORDER BY al.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_transaction_summary(self):
        """Get a summary of transactions by type."""
        rows = self.db.execute(
            """SELECT transaction_type,
                      COUNT(*) as count,
                      COALESCE(SUM(amount), 0) as total_amount
               FROM transactions
               GROUP BY transaction_type"""
        ).fetchall()
        return [dict(r) for r in rows]
