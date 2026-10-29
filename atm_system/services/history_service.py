"""
Module 4: Transaction History Service
=======================================
Provides transaction history viewing, statement generation, and
filtering capabilities for account holders.
"""
from datetime import datetime, timedelta


class HistoryService:
    """Manages transaction history retrieval and filtering."""

    def __init__(self, db_manager):
        self.db = db_manager

    def get_recent_transactions(self, account_id, limit=10):
        """Get the most recent transactions for an account."""
        rows = self.db.execute(
            """SELECT t.*, a.account_number
               FROM transactions t
               JOIN accounts a ON t.account_id = a.id
               WHERE t.account_id = ?
               ORDER BY t.created_at DESC
               LIMIT ?""",
            (account_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_transactions_by_date_range(self, account_id, start_date, end_date):
        """Get transactions within a specific date range."""
        rows = self.db.execute(
            """SELECT t.*, a.account_number
               FROM transactions t
               JOIN accounts a ON t.account_id = a.id
               WHERE t.account_id = ?
                 AND date(t.created_at) BETWEEN ? AND ?
               ORDER BY t.created_at DESC""",
            (account_id, start_date, end_date),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_transactions_by_type(self, account_id, transaction_type):
        """Get transactions filtered by type."""
        rows = self.db.execute(
            """SELECT t.*, a.account_number
               FROM transactions t
               JOIN accounts a ON t.account_id = a.id
               WHERE t.account_id = ? AND t.transaction_type = ?
               ORDER BY t.created_at DESC""",
            (account_id, transaction_type),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_statement(self, account_id, days=30):
        """Generate a mini-statement for the last N days."""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        transactions = self.get_transactions_by_date_range(
            account_id, start_date, end_date
        )

        # Compute summary statistics
        total_deposits = sum(
            t["amount"] for t in transactions if t["transaction_type"] == "deposit"
        )
        total_withdrawals = sum(
            t["amount"] for t in transactions if t["transaction_type"] == "withdrawal"
        )
        total_transfers_out = sum(
            t["amount"] for t in transactions if t["transaction_type"] == "transfer"
        )
        total_transfers_in = sum(
            t["amount"] for t in transactions if t["transaction_type"] == "transfer_in"
        )

        return {
            "account_id": account_id,
            "period_start": start_date,
            "period_end": end_date,
            "transaction_count": len(transactions),
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "total_transfers_out": total_transfers_out,
            "total_transfers_in": total_transfers_in,
            "net_change": (
                total_deposits + total_transfers_in
                - total_withdrawals - total_transfers_out
            ),
            "transactions": transactions,
        }

    def get_all_transactions(self, limit=100):
        """Get all transactions system-wide (admin use)."""
        rows = self.db.execute(
            """SELECT t.*, a.account_number, u.full_name
               FROM transactions t
               JOIN accounts a ON t.account_id = a.id
               JOIN users u ON a.user_id = u.id
               ORDER BY t.created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_notifications(self, user_id, unread_only=False):
        """Get notifications for a user."""
        if unread_only:
            rows = self.db.execute(
                """SELECT * FROM notifications
                   WHERE user_id = ? AND is_read = 0
                   ORDER BY created_at DESC""",
                (user_id,),
            ).fetchall()
        else:
            rows = self.db.execute(
                """SELECT * FROM notifications
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT 50""",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        self.db.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,),
        )
        self.db.commit()

    def mark_all_notifications_read(self, user_id):
        """Mark all notifications as read for a user."""
        self.db.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (user_id,),
        )
        self.db.commit()
