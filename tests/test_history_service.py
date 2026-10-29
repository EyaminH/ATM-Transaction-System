"""Unit tests for HistoryService (Recent transactions, filtering, statements, notifications)."""
from datetime import datetime


class TestHistoryService:
    """Verifies transaction history query options and statement metrics."""

    def test_recent_transactions_and_filtering(
        self, history_service, transaction_service, sample_user
    ):
        acc = sample_user["account"]
        user_id = sample_user["user"]["id"]

        transaction_service.deposit(acc["id"], 1000.0, user_id=user_id)
        transaction_service.withdraw(acc["id"], 500.0, user_id=user_id)
        transaction_service.deposit(acc["id"], 2000.0, user_id=user_id)

        recent = history_service.get_recent_transactions(acc["id"], limit=2)
        assert len(recent) == 2

        deposits = history_service.get_transactions_by_type(acc["id"], "deposit")
        assert len(deposits) == 2
        assert all(t["transaction_type"] == "deposit" for t in deposits)

        withdrawals = history_service.get_transactions_by_type(acc["id"], "withdrawal")
        assert len(withdrawals) == 1
        assert withdrawals[0]["amount"] == 500.0

    def test_get_statement_computes_metrics(
        self, history_service, transaction_service, sample_user
    ):
        acc = sample_user["account"]
        user_id = sample_user["user"]["id"]

        transaction_service.deposit(acc["id"], 5000.0, user_id=user_id)
        transaction_service.withdraw(acc["id"], 2000.0, user_id=user_id)

        stmt = history_service.get_statement(acc["id"], days=7)
        assert stmt["total_deposits"] == 5000.0
        assert stmt["total_withdrawals"] == 2000.0
        assert stmt["net_change"] == 3000.0
        assert stmt["transaction_count"] == 2

    def test_notifications_lifecycle(self, history_service, test_db, sample_user):
        user_id = sample_user["user"]["id"]

        test_db.execute(
            "INSERT INTO notifications (user_id, message, is_read) VALUES (?, 'Notif 1', 0)",
            (user_id,),
        )
        test_db.execute(
            "INSERT INTO notifications (user_id, message, is_read) VALUES (?, 'Notif 2', 0)",
            (user_id,),
        )
        test_db.commit()

        unread = history_service.get_notifications(user_id, unread_only=True)
        assert len(unread) == 2

        # Mark single read
        history_service.mark_notification_read(unread[0]["id"])
        unread_after = history_service.get_notifications(user_id, unread_only=True)
        assert len(unread_after) == 1

        # Mark all read
        history_service.mark_all_notifications_read(user_id)
        unread_final = history_service.get_notifications(user_id, unread_only=True)
        assert len(unread_final) == 0
