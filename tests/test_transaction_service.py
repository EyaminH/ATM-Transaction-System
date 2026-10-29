"""Unit tests for TransactionService (Withdraw, Deposit, Transfer, Observer notifications)."""


class TestTransactionService:
    """Verifies transaction operations, error scenarios, and observer side-effects."""

    def test_withdraw_success_and_notification(self, transaction_service, sample_user, test_db):
        acc = sample_user["account"]
        user_id = sample_user["user"]["id"]

        result = transaction_service.withdraw(acc["id"], 2500.0, user_id=user_id)
        assert result["success"] is True
        assert result["balance_after"] == 7500.0

        # Verify notification created
        notifs = test_db.execute(
            "SELECT * FROM notifications WHERE user_id = ?", (user_id,)
        ).fetchall()
        assert len(notifs) >= 1
        assert "Withdrawal of ৳2500.00" in notifs[-1]["message"]

    def test_withdraw_nonexistent_or_inactive_account(self, transaction_service, sample_user, account_service):
        res = transaction_service.withdraw(99999, 1000.0)
        assert res["success"] is False
        assert "Account not found" in res["errors"][0]

        acc = sample_user["account"]
        account_service.deactivate_account(acc["id"])
        res_inactive = transaction_service.withdraw(acc["id"], 1000.0)
        assert res_inactive["success"] is False
        assert "inactive" in res_inactive["errors"][0]

    def test_deposit_success_and_audit(self, transaction_service, sample_user, test_db):
        acc = sample_user["account"]
        user_id = sample_user["user"]["id"]

        result = transaction_service.deposit(acc["id"], 3000.0, user_id=user_id)
        assert result["success"] is True
        assert result["balance_after"] == 13000.0

        # Verify audit log entry
        audit = test_db.execute(
            "SELECT * FROM audit_log WHERE user_id = ? AND action = 'deposit'", (user_id,)
        ).fetchall()
        assert len(audit) >= 1

    def test_transfer_success_both_users_notified(
        self, transaction_service, sample_user, auth_service, account_service, test_db
    ):
        sender_acc = sample_user["account"]
        sender_user = sample_user["user"]

        _, rec_user = auth_service.register_user("4444555566667777", "9876", "Receiver User")
        rec_acc = account_service.create_account(rec_user["id"], "savings", 2000.0)

        result = transaction_service.transfer(
            sender_acc["id"], rec_acc["account_number"], 4000.0, user_id=sender_user["id"]
        )
        assert result["success"] is True
        assert result["balance_after"] == 6000.0

        # Sender notification
        sender_notifs = test_db.execute(
            "SELECT * FROM notifications WHERE user_id = ?", (sender_user["id"],)
        ).fetchall()
        assert any("Transfer of ৳4000.00" in n["message"] for n in sender_notifs)

        # Receiver notification
        rec_notifs = test_db.execute(
            "SELECT * FROM notifications WHERE user_id = ?", (rec_user["id"],)
        ).fetchall()
        assert any("Received ৳4000.00" in n["message"] for n in rec_notifs)

    def test_transfer_missing_target(self, transaction_service, sample_user):
        acc = sample_user["account"]
        res = transaction_service.transfer(acc["id"], "NON-EXISTENT", 500.0)
        assert res["success"] is False
        assert "Target account not found" in res["errors"][0]
