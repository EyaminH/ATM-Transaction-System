"""Unit tests for AdminService (Metrics, User management, Lock reset, Audit logs)."""


class TestAdminService:
    """Verifies administrative operations and system analytics."""

    def test_get_system_stats(self, admin_service, sample_user, sample_admin, transaction_service):
        acc = sample_user["account"]
        transaction_service.deposit(acc["id"], 1500.0)

        stats = admin_service.get_system_stats()
        assert stats["total_users"] >= 2
        assert stats["active_users"] >= 2
        assert stats["total_accounts"] >= 2
        assert stats["total_balance"] > 0
        assert stats["total_transactions"] >= 1

    def test_toggle_user_status(self, admin_service, sample_user):
        user_id = sample_user["user"]["id"]

        success, msg = admin_service.toggle_user_status(user_id)
        assert success is True
        assert "deactivated" in msg

        users = admin_service.get_all_users()
        target = next(u for u in users if u["id"] == user_id)
        assert target["is_active"] == 0

        # Toggle back
        success2, msg2 = admin_service.toggle_user_status(user_id)
        assert success2 is True
        assert "activated" in msg2

    def test_unlock_user(self, admin_service, auth_service, sample_user):
        card = sample_user["user"]["card_number"]
        user_id = sample_user["user"]["id"]

        # Cause 3 failed logins to lock user
        for _ in range(3):
            auth_service.authenticate(card, "wrong")

        # Confirm locked
        users = admin_service.get_all_users()
        target = next(u for u in users if u["id"] == user_id)
        assert target["login_attempts"] >= 3

        # Unlock user via admin service
        success, msg = admin_service.unlock_user(user_id)
        assert success is True
        assert "unlocked" in msg

        # Should be able to authenticate with correct PIN again
        auth_success, _ = auth_service.authenticate(card, "1234")
        assert auth_success is True

    def test_get_audit_log_and_transaction_summary(
        self, admin_service, transaction_service, sample_user
    ):
        acc = sample_user["account"]
        transaction_service.deposit(acc["id"], 2000.0)
        transaction_service.withdraw(acc["id"], 500.0)

        logs = admin_service.get_audit_log(limit=10)
        assert len(logs) >= 2

        summary = admin_service.get_transaction_summary()
        assert len(summary) >= 2
        types = [s["transaction_type"] for s in summary]
        assert "deposit" in types
        assert "withdrawal" in types
