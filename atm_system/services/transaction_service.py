"""
Module 3: Transaction Processing Service
==========================================
Core transaction module that uses the Strategy pattern for withdrawal,
deposit, and transfer operations, and the Observer pattern for
notifying subscribers.
"""
from atm_system.patterns.strategy import (
    TransactionContext,
    WithdrawalStrategy,
    DepositStrategy,
    TransferStrategy,
)
from atm_system.services.account_service import AccountService


class TransactionService:
    """
    Orchestrates ATM transactions using the Strategy and Observer patterns.
    """

    def __init__(self, db_manager, config, event_manager=None):
        self.db = db_manager
        self.config = config
        self.event_manager = event_manager
        self.account_service = AccountService(db_manager)

        # Pre-create strategy instances
        self._strategies = {
            "withdrawal": WithdrawalStrategy(config),
            "deposit": DepositStrategy(config),
            "transfer": TransferStrategy(config),
        }

    def _notify(self, event_type, data):
        """Helper to notify observers if an event manager is attached."""
        if self.event_manager:
            self.event_manager.notify(event_type, data)

    def withdraw(self, account_id, amount, user_id=None):
        """Process a cash withdrawal."""
        account = self.account_service.get_account_by_id(account_id)
        if not account:
            return {"success": False, "errors": ["Account not found."]}
        if not account["is_active"]:
            return {"success": False, "errors": ["Account is inactive."]}

        context = TransactionContext(self._strategies["withdrawal"])
        result = context.process(account, amount, self.db)

        if result["success"]:
            self._notify("withdrawal", {
                "user_id": user_id,
                "account_id": account_id,
                "amount": amount,
                "balance_after": result["balance_after"],
                "status": "completed",
            })

        return result

    def deposit(self, account_id, amount, user_id=None):
        """Process a cash deposit."""
        account = self.account_service.get_account_by_id(account_id)
        if not account:
            return {"success": False, "errors": ["Account not found."]}
        if not account["is_active"]:
            return {"success": False, "errors": ["Account is inactive."]}

        context = TransactionContext(self._strategies["deposit"])
        result = context.process(account, amount, self.db)

        if result["success"]:
            self._notify("deposit", {
                "user_id": user_id,
                "account_id": account_id,
                "amount": amount,
                "balance_after": result["balance_after"],
                "status": "completed",
            })

        return result

    def transfer(self, account_id, target_account_number, amount, user_id=None):
        """Process a fund transfer to another account."""
        account = self.account_service.get_account_by_id(account_id)
        if not account:
            return {"success": False, "errors": ["Source account not found."]}
        if not account["is_active"]:
            return {"success": False, "errors": ["Source account is inactive."]}

        target_account = self.account_service.get_account_by_number(
            target_account_number
        )
        if not target_account:
            return {"success": False, "errors": ["Target account not found."]}

        context = TransactionContext(self._strategies["transfer"])
        result = context.process(
            account, amount, self.db, target_account=target_account
        )

        if result["success"]:
            # Notify sender
            self._notify("transfer", {
                "user_id": user_id,
                "account_id": account_id,
                "amount": amount,
                "balance_after": result["balance_after"],
                "target_account": target_account_number,
                "status": "completed",
            })
            # Notify receiver
            target_user = self.db.execute(
                "SELECT user_id FROM accounts WHERE id = ?",
                (target_account["id"],),
            ).fetchone()
            if target_user:
                self._notify("transfer_in", {
                    "user_id": target_user["user_id"],
                    "account_id": target_account["id"],
                    "amount": amount,
                    "balance_after": target_account["balance"] + amount,
                    "source_account": account["account_number"],
                    "status": "completed",
                })

        return result
