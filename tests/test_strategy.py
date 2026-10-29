"""Unit tests for Strategy Pattern (Transaction Strategies)."""
from atm_system.patterns.strategy import (
    WithdrawalStrategy,
    DepositStrategy,
    TransferStrategy,
)
from tests.conftest import TestConfig


class TestWithdrawalStrategy:
    """Tests for WithdrawalStrategy validation and execution."""

    def test_validate_negative_or_zero_amount(self):
        strategy = WithdrawalStrategy(TestConfig)
        account = {"id": 1, "balance": 5000.0, "daily_withdrawn": 0.0, "last_withdrawal_date": None}
        errors = strategy.validate(account, 0.0)
        assert any("positive" in e for e in errors)
        errors_neg = strategy.validate(account, -50.0)
        assert any("positive" in e for e in errors_neg)

    def test_validate_below_minimum_amount(self):
        strategy = WithdrawalStrategy(TestConfig)
        account = {"id": 1, "balance": 5000.0, "daily_withdrawn": 0.0, "last_withdrawal_date": None}
        errors = strategy.validate(account, TestConfig.MIN_WITHDRAWAL_AMOUNT - 10)
        assert any("Minimum withdrawal" in e for e in errors)

    def test_validate_above_maximum_amount(self):
        strategy = WithdrawalStrategy(TestConfig)
        account = {"id": 1, "balance": 50000.0, "daily_withdrawn": 0.0, "last_withdrawal_date": None}
        errors = strategy.validate(account, TestConfig.MAX_WITHDRAWAL_AMOUNT + 500)
        assert any("Maximum withdrawal" in e for e in errors)

    def test_validate_insufficient_balance(self):
        strategy = WithdrawalStrategy(TestConfig)
        account = {"id": 1, "balance": 1000.0, "daily_withdrawn": 0.0, "last_withdrawal_date": None}
        errors = strategy.validate(account, 1500.0)
        assert any("Insufficient balance" in e for e in errors)

    def test_validate_daily_limit_exceeded(self):
        strategy = WithdrawalStrategy(TestConfig)
        account = {
            "id": 1,
            "balance": 100000.0,
            "daily_withdrawn": TestConfig.DAILY_WITHDRAWAL_LIMIT - 100,
            "last_withdrawal_date": "2026-10-30",
        }
        from datetime import date
        account["last_withdrawal_date"] = str(date.today())
        errors = strategy.validate(account, 500.0)
        assert any("Daily withdrawal limit exceeded" in e for e in errors)

    def test_execute_successful_withdrawal(self, test_db, account_service, sample_user):
        acc = sample_user["account"]
        strategy = WithdrawalStrategy(TestConfig)
        initial_balance = acc["balance"]
        withdraw_amount = 2000.0

        errors = strategy.validate(acc, withdraw_amount)
        assert not errors

        res = strategy.execute(acc, withdraw_amount, test_db)
        assert res["success"] is True
        assert res["balance_after"] == initial_balance - withdraw_amount

        updated_acc = account_service.get_account_by_id(acc["id"])
        assert updated_acc["balance"] == initial_balance - withdraw_amount


class TestDepositStrategy:
    """Tests for DepositStrategy validation and execution."""

    def test_validate_invalid_amounts(self):
        strategy = DepositStrategy(TestConfig)
        account = {"id": 1, "balance": 1000.0}
        assert any("positive" in e for e in strategy.validate(account, -100))
        assert any("Minimum deposit" in e for e in strategy.validate(account, TestConfig.MIN_DEPOSIT_AMOUNT - 50))

    def test_execute_deposit(self, test_db, account_service, sample_user):
        acc = sample_user["account"]
        strategy = DepositStrategy(TestConfig)
        initial_balance = acc["balance"]
        deposit_amount = 5000.0

        errors = strategy.validate(acc, deposit_amount)
        assert not errors

        res = strategy.execute(acc, deposit_amount, test_db)
        assert res["success"] is True
        assert res["balance_after"] == initial_balance + deposit_amount

        updated_acc = account_service.get_account_by_id(acc["id"])
        assert updated_acc["balance"] == initial_balance + deposit_amount


class TestTransferStrategy:
    """Tests for TransferStrategy validation and execution."""

    def test_validate_self_transfer(self):
        strategy = TransferStrategy(TestConfig)
        account = {"id": 1, "balance": 5000.0}
        target = {"id": 1, "balance": 2000.0, "is_active": 1}
        errors = strategy.validate(account, 1000.0, target_account=target)
        assert any("Cannot transfer to the same account" in e for e in errors)

    def test_validate_inactive_or_missing_target(self):
        strategy = TransferStrategy(TestConfig)
        account = {"id": 1, "balance": 5000.0}
        errors = strategy.validate(account, 1000.0, target_account=None)
        assert any("Target account not found" in e for e in errors)

        inactive_target = {"id": 2, "balance": 1000.0, "is_active": 0}
        errors_inactive = strategy.validate(account, 1000.0, target_account=inactive_target)
        assert any("inactive" in e for e in errors_inactive)

    def test_execute_transfer(self, test_db, account_service, auth_service, sample_user):
        sender = sample_user["account"]
        _, rec_user = auth_service.register_user(
            card_number="3333444455556666",
            pin="1111",
            full_name="Bob Receiver",
        )
        receiver = account_service.create_account(rec_user["id"], "savings", 1000.0)

        strategy = TransferStrategy(TestConfig)
        transfer_amount = 3000.0

        errors = strategy.validate(sender, transfer_amount, target_account=receiver)
        assert not errors

        res = strategy.execute(sender, transfer_amount, test_db, target_account=receiver)
        assert res["success"] is True
        assert res["balance_after"] == sender["balance"] - transfer_amount

        # Check sender and receiver balances in DB
        sender_db = account_service.get_account_by_id(sender["id"])
        rec_db = account_service.get_account_by_id(receiver["id"])
        assert sender_db["balance"] == sender["balance"] - transfer_amount
        assert rec_db["balance"] == receiver["balance"] + transfer_amount
