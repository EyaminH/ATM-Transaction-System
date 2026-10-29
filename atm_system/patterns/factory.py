"""
Factory Method Pattern (Creational)
====================================
Problem it solves:
    Transaction objects need different initialization depending on their
    type (withdrawal, deposit, transfer). The Factory Method encapsulates
    the creation logic, letting the client request a transaction by type
    without knowing the concrete construction details.

Alternative rejected:
    Constructor overloading / multiple __init__ signatures — Python
    doesn't support true overloading, so using kwargs with complex
    conditionals inside __init__ leads to fragile code. The Factory
    Method keeps each creation path explicit and testable.
"""


class Transaction:
    """Represents a single ATM transaction record."""

    def __init__(
        self,
        transaction_type,
        amount,
        account_id,
        balance_before,
        balance_after,
        target_account_id=None,
        description="",
        status="completed",
    ):
        self.transaction_type = transaction_type
        self.amount = amount
        self.account_id = account_id
        self.balance_before = balance_before
        self.balance_after = balance_after
        self.target_account_id = target_account_id
        self.description = description
        self.status = status

    def to_dict(self):
        """Serialize the transaction to a dictionary."""
        return {
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "account_id": self.account_id,
            "balance_before": self.balance_before,
            "balance_after": self.balance_after,
            "target_account_id": self.target_account_id,
            "description": self.description,
            "status": self.status,
        }

    def __repr__(self):
        return (
            f"Transaction(type={self.transaction_type}, "
            f"amount={self.amount}, status={self.status})"
        )


class TransactionFactory:
    """
    Factory Method for creating Transaction objects.
    Encapsulates the construction logic for each transaction type.
    """

    @staticmethod
    def create_withdrawal(account_id, amount, balance_before):
        """Create a withdrawal transaction."""
        return Transaction(
            transaction_type="withdrawal",
            amount=amount,
            account_id=account_id,
            balance_before=balance_before,
            balance_after=balance_before - amount,
            description=f"ATM Cash Withdrawal of ৳{amount:.2f}",
        )

    @staticmethod
    def create_deposit(account_id, amount, balance_before):
        """Create a deposit transaction."""
        return Transaction(
            transaction_type="deposit",
            amount=amount,
            account_id=account_id,
            balance_before=balance_before,
            balance_after=balance_before + amount,
            description=f"ATM Cash Deposit of ৳{amount:.2f}",
        )

    @staticmethod
    def create_transfer(
        account_id, amount, balance_before, target_account_id
    ):
        """Create a transfer transaction."""
        return Transaction(
            transaction_type="transfer",
            amount=amount,
            account_id=account_id,
            balance_before=balance_before,
            balance_after=balance_before - amount,
            target_account_id=target_account_id,
            description=f"Fund Transfer of ৳{amount:.2f}",
        )

    @classmethod
    def create(cls, transaction_type, **kwargs):
        """
        Factory method — create a transaction by type string.
        Delegates to the appropriate static constructor.
        """
        creators = {
            "withdrawal": cls.create_withdrawal,
            "deposit": cls.create_deposit,
            "transfer": cls.create_transfer,
        }
        creator = creators.get(transaction_type)
        if creator is None:
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        return creator(**kwargs)
