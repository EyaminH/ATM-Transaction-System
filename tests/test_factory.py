"""Unit tests for Factory Method Pattern (TransactionFactory)."""
import pytest
from atm_system.patterns.factory import Transaction, TransactionFactory


class TestTransactionFactory:
    """Verifies factory creation and serialization of transactions."""

    def test_create_withdrawal_explicit(self):
        tx = TransactionFactory.create_withdrawal(
            account_id=1, amount=500.0, balance_before=2000.0
        )
        assert isinstance(tx, Transaction)
        assert tx.transaction_type == "withdrawal"
        assert tx.amount == 500.0
        assert tx.balance_before == 2000.0
        assert tx.balance_after == 1500.0
        assert "Withdrawal" in tx.description

    def test_create_deposit_explicit(self):
        tx = TransactionFactory.create_deposit(
            account_id=2, amount=1000.0, balance_before=3000.0
        )
        assert tx.transaction_type == "deposit"
        assert tx.amount == 1000.0
        assert tx.balance_after == 4000.0
        assert "Deposit" in tx.description

    def test_create_transfer_explicit(self):
        tx = TransactionFactory.create_transfer(
            account_id=1, amount=750.0, balance_before=5000.0, target_account_id=3
        )
        assert tx.transaction_type == "transfer"
        assert tx.amount == 750.0
        assert tx.balance_after == 4250.0
        assert tx.target_account_id == 3

    def test_dynamic_create_dispatch(self):
        tx = TransactionFactory.create(
            "withdrawal", account_id=1, amount=200.0, balance_before=1000.0
        )
        assert tx.transaction_type == "withdrawal"
        assert tx.amount == 200.0

    def test_unknown_transaction_type_raises(self):
        with pytest.raises(ValueError, match="Unknown transaction type"):
            TransactionFactory.create("crypto_swap", account_id=1, amount=100.0, balance_before=500.0)

    def test_transaction_to_dict_and_repr(self):
        tx = TransactionFactory.create_withdrawal(
            account_id=1, amount=100.0, balance_before=500.0
        )
        data = tx.to_dict()
        assert isinstance(data, dict)
        assert data["transaction_type"] == "withdrawal"
        assert data["amount"] == 100.0
        assert "Transaction(type=withdrawal" in repr(tx)
