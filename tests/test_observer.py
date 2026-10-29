"""Unit tests for Observer Pattern (Transaction Events & Mocks)."""
from unittest.mock import MagicMock
from atm_system.patterns.observer import (
    TransactionEventManager,
    TransactionObserver,
    NotificationObserver,
    AuditLogObserver,
)


class MockExternalSMSGateway(TransactionObserver):
    """External dependency simulation for SMS alerts."""

    def __init__(self, client):
        self.client = client

    def update(self, event_type, data):
        phone = data.get("phone", "+8801700000000")
        msg = f"Alert: {event_type} of ৳{data.get('amount', 0)}"
        self.client.send_sms(to=phone, body=msg)


class TestObserverPattern:
    """Verifies publish-subscribe mechanics, notification and audit logging."""

    def test_subscribe_and_notify(self):
        manager = TransactionEventManager()
        observer = MagicMock(spec=TransactionObserver)

        manager.subscribe("withdrawal", observer)
        event_data = {"user_id": 1, "amount": 1000.0, "balance_after": 4000.0}
        manager.notify("withdrawal", event_data)

        observer.update.assert_called_once_with("withdrawal", event_data)

    def test_unsubscribe(self):
        manager = TransactionEventManager()
        observer = MagicMock(spec=TransactionObserver)

        manager.subscribe("deposit", observer)
        manager.unsubscribe("deposit", observer)

        manager.notify("deposit", {"user_id": 1, "amount": 500.0})
        observer.update.assert_not_called()

    def test_notification_observer_creates_db_record(self, test_db, sample_user):
        user_id = sample_user["user"]["id"]
        obs = NotificationObserver(test_db)

        obs.update("withdrawal", {
            "user_id": user_id,
            "amount": 2500.0,
            "balance_after": 7500.0,
        })

        notifs = test_db.execute(
            "SELECT * FROM notifications WHERE user_id = ?", (user_id,)
        ).fetchall()
        assert len(notifs) == 1
        assert "Withdrawal of ৳2500.00" in notifs[0]["message"]

    def test_audit_log_observer_records_security_trail(self, test_db, sample_user):
        user_id = sample_user["user"]["id"]
        obs = AuditLogObserver(test_db)

        obs.update("login_failed", {
            "user_id": user_id,
            "account_id": None,
            "status": "failed",
        })

        logs = test_db.execute(
            "SELECT * FROM audit_log WHERE user_id = ?", (user_id,)
        ).fetchall()
        assert len(logs) == 1
        assert logs[0]["action"] == "login_failed"

    def test_mock_external_sms_dependency(self):
        """TDD mock test verifying isolation of external third-party services."""
        mock_gateway = MagicMock()
        sms_observer = MockExternalSMSGateway(mock_gateway)

        manager = TransactionEventManager()
        manager.subscribe("transfer", sms_observer)

        manager.notify("transfer", {
            "user_id": 42,
            "phone": "+8801711223344",
            "amount": 5000.0,
        })

        mock_gateway.send_sms.assert_called_once_with(
            to="+8801711223344",
            body="Alert: transfer of ৳5000.0",
        )
