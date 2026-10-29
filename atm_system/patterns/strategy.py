"""
Strategy Pattern (Behavioral)
==============================
Problem it solves:
    Different transaction types (withdrawal, deposit, transfer) require
    different processing logic — validation rules, balance updates, and
    side effects all differ. The Strategy pattern allows us to swap the
    transaction algorithm at runtime without modifying the context class.

Alternative rejected:
    Large if/elif chain — placing all transaction logic inside a single
    method with conditionals makes the code hard to extend (adding a new
    transaction type means modifying existing code, violating the
    Open/Closed Principle).
"""
from abc import ABC, abstractmethod
from datetime import date


class TransactionStrategy(ABC):
    """Abstract base class for transaction strategies."""

    @abstractmethod
    def validate(self, account, amount, **kwargs):
        """Validate whether the transaction can be performed."""
        pass

    @abstractmethod
    def execute(self, account, amount, db_manager, **kwargs):
        """Execute the transaction and return the result."""
        pass

    @abstractmethod
    def get_description(self, amount, **kwargs):
        """Return a human-readable description of the transaction."""
        pass


class WithdrawalStrategy(TransactionStrategy):
    """Strategy for processing cash withdrawals."""

    def __init__(self, config):
        self.config = config

    def validate(self, account, amount, **kwargs):
        """
        Validate withdrawal:
        - Amount must be positive and within limits
        - Sufficient balance (maintaining minimum)
        - Daily withdrawal limit not exceeded
        """
        errors = []
        if amount <= 0:
            errors.append("Withdrawal amount must be positive.")
        if amount < self.config.MIN_WITHDRAWAL_AMOUNT:
            errors.append(
                f"Minimum withdrawal is ৳{self.config.MIN_WITHDRAWAL_AMOUNT:.2f}."
            )
        if amount > self.config.MAX_WITHDRAWAL_AMOUNT:
            errors.append(
                f"Maximum withdrawal is ৳{self.config.MAX_WITHDRAWAL_AMOUNT:.2f}."
            )
        available_balance = account["balance"] - self.config.MIN_BALANCE
        if amount > available_balance:
            errors.append(
                f"Insufficient balance. Available: ৳{available_balance:.2f} "
                f"(৳{self.config.MIN_BALANCE:.2f} minimum balance required)."
            )

        # Check daily withdrawal limit
        today = str(date.today())
        daily_withdrawn = account["daily_withdrawn"]
        if account["last_withdrawal_date"] != today:
            daily_withdrawn = 0.0
        if daily_withdrawn + amount > self.config.DAILY_WITHDRAWAL_LIMIT:
            remaining = self.config.DAILY_WITHDRAWAL_LIMIT - daily_withdrawn
            errors.append(
                f"Daily withdrawal limit exceeded. Remaining today: ৳{remaining:.2f}."
            )

        return errors

    def execute(self, account, amount, db_manager, **kwargs):
        """Execute a withdrawal transaction."""
        balance_before = account["balance"]
        balance_after = balance_before - amount
        today = str(date.today())

        daily_withdrawn = account["daily_withdrawn"]
        if account["last_withdrawal_date"] != today:
            daily_withdrawn = 0.0
        daily_withdrawn += amount

        # Update account balance and daily withdrawal tracking
        db_manager.execute(
            """UPDATE accounts
               SET balance = ?, daily_withdrawn = ?, last_withdrawal_date = ?,
                   updated_at = datetime('now')
               WHERE id = ?""",
            (balance_after, daily_withdrawn, today, account["id"]),
        )

        # Record transaction
        db_manager.execute(
            """INSERT INTO transactions
               (account_id, transaction_type, amount, balance_before,
                balance_after, description, status)
               VALUES (?, 'withdrawal', ?, ?, ?, ?, 'completed')""",
            (
                account["id"],
                amount,
                balance_before,
                balance_after,
                self.get_description(amount),
            ),
        )
        db_manager.commit()

        return {
            "success": True,
            "transaction_type": "withdrawal",
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "message": f"৳{amount:.2f} withdrawn successfully.",
        }

    def get_description(self, amount, **kwargs):
        return f"ATM Cash Withdrawal of ৳{amount:.2f}"


class DepositStrategy(TransactionStrategy):
    """Strategy for processing cash deposits."""

    def __init__(self, config):
        self.config = config

    def validate(self, account, amount, **kwargs):
        """Validate deposit — amount must be positive and above minimum."""
        errors = []
        if amount <= 0:
            errors.append("Deposit amount must be positive.")
        if amount < self.config.MIN_DEPOSIT_AMOUNT:
            errors.append(
                f"Minimum deposit is ৳{self.config.MIN_DEPOSIT_AMOUNT:.2f}."
            )
        return errors

    def execute(self, account, amount, db_manager, **kwargs):
        """Execute a deposit transaction."""
        balance_before = account["balance"]
        balance_after = balance_before + amount

        db_manager.execute(
            """UPDATE accounts
               SET balance = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (balance_after, account["id"]),
        )

        db_manager.execute(
            """INSERT INTO transactions
               (account_id, transaction_type, amount, balance_before,
                balance_after, description, status)
               VALUES (?, 'deposit', ?, ?, ?, ?, 'completed')""",
            (
                account["id"],
                amount,
                balance_before,
                balance_after,
                self.get_description(amount),
            ),
        )
        db_manager.commit()

        return {
            "success": True,
            "transaction_type": "deposit",
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "message": f"৳{amount:.2f} deposited successfully.",
        }

    def get_description(self, amount, **kwargs):
        return f"ATM Cash Deposit of ৳{amount:.2f}"


class TransferStrategy(TransactionStrategy):
    """Strategy for processing fund transfers between accounts."""

    def __init__(self, config):
        self.config = config

    def validate(self, account, amount, **kwargs):
        """
        Validate transfer:
        - Amount positive, sufficient balance
        - Target account exists and is active
        - Cannot transfer to self
        """
        target_account = kwargs.get("target_account")
        errors = []

        if amount <= 0:
            errors.append("Transfer amount must be positive.")
        if amount < self.config.MIN_WITHDRAWAL_AMOUNT:
            errors.append(
                f"Minimum transfer is ৳{self.config.MIN_WITHDRAWAL_AMOUNT:.2f}."
            )
        available = account["balance"] - self.config.MIN_BALANCE
        if amount > available:
            errors.append(
                f"Insufficient balance. Available: ৳{available:.2f}."
            )
        if target_account is None:
            errors.append("Target account not found.")
        elif target_account["id"] == account["id"]:
            errors.append("Cannot transfer to the same account.")
        elif not target_account["is_active"]:
            errors.append("Target account is inactive.")

        return errors

    def execute(self, account, amount, db_manager, **kwargs):
        """Execute a fund transfer between accounts."""
        target_account = kwargs["target_account"]
        balance_before = account["balance"]
        balance_after = balance_before - amount
        target_balance_before = target_account["balance"]
        target_balance_after = target_balance_before + amount

        # Debit sender
        db_manager.execute(
            """UPDATE accounts
               SET balance = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (balance_after, account["id"]),
        )
        # Credit receiver
        db_manager.execute(
            """UPDATE accounts
               SET balance = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (target_balance_after, target_account["id"]),
        )

        # Record debit transaction
        db_manager.execute(
            """INSERT INTO transactions
               (account_id, transaction_type, amount, balance_before,
                balance_after, target_account_id, description, status)
               VALUES (?, 'transfer', ?, ?, ?, ?, ?, 'completed')""",
            (
                account["id"],
                amount,
                balance_before,
                balance_after,
                target_account["id"],
                self.get_description(amount, target_account=target_account),
            ),
        )

        # Record credit transaction on target
        db_manager.execute(
            """INSERT INTO transactions
               (account_id, transaction_type, amount, balance_before,
                balance_after, target_account_id, description, status)
               VALUES (?, 'transfer_in', ?, ?, ?, ?, ?, 'completed')""",
            (
                target_account["id"],
                amount,
                target_balance_before,
                target_balance_after,
                account["id"],
                f"Transfer received from account {account['account_number']}",
            ),
        )
        db_manager.commit()

        return {
            "success": True,
            "transaction_type": "transfer",
            "amount": amount,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "target_account": target_account["account_number"],
            "message": f"৳{amount:.2f} transferred successfully to {target_account['account_number']}.",
        }

    def get_description(self, amount, **kwargs):
        target = kwargs.get("target_account", {})
        target_num = target.get("account_number", "unknown")
        return f"Fund Transfer of ৳{amount:.2f} to account {target_num}"


class TransactionContext:
    """
    Context class that uses a TransactionStrategy.
    Delegates transaction processing to the active strategy.
    """

    def __init__(self, strategy: TransactionStrategy):
        self._strategy = strategy

    @property
    def strategy(self):
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: TransactionStrategy):
        self._strategy = strategy

    def process(self, account, amount, db_manager, **kwargs):
        """Validate and execute the transaction using the current strategy."""
        errors = self._strategy.validate(account, amount, **kwargs)
        if errors:
            return {"success": False, "errors": errors}
        return self._strategy.execute(account, amount, db_manager, **kwargs)
