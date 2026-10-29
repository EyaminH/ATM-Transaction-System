"""
Observer Pattern (Behavioral)
==============================
Problem it solves:
    When a transaction occurs, multiple subsystems need to be notified —
    the notification service stores an alert for the user, the audit log
    records the event, and (optionally) an email/SMS could be sent. The
    Observer pattern decouples the transaction processing from these
    side effects so new observers can be added without modifying the
    transaction code.

Alternative rejected:
    Direct method calls — calling notification/audit methods directly
    inside the transaction service creates tight coupling and makes it
    impossible to add new side effects without editing the transaction
    service. The Observer pattern follows the Open/Closed Principle.
"""
from abc import ABC, abstractmethod
from datetime import datetime


class TransactionObserver(ABC):
    """Abstract observer that reacts to transaction events."""

    @abstractmethod
    def update(self, event_type, data):
        """Called when a transaction event occurs."""
        pass


class NotificationObserver(TransactionObserver):
    """
    Observer that creates in-app notifications for the account holder
    whenever a transaction is processed.
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def update(self, event_type, data):
        """Create a notification record for the user."""
        user_id = data.get("user_id")
        if not user_id:
            return

        amount = data.get("amount", 0.0)
        balance_after = data.get("balance_after", 0.0)

        if event_type == "withdrawal":
            message = (
                f"Withdrawal of ৳{amount:.2f} completed. "
                f"Balance: ৳{balance_after:.2f}"
            )
        elif event_type == "deposit":
            message = (
                f"Deposit of ৳{amount:.2f} completed. "
                f"Balance: ৳{balance_after:.2f}"
            )
        elif event_type == "transfer":
            message = (
                f"Transfer of ৳{amount:.2f} to {data.get('target_account', 'N/A')} completed. "
                f"Balance: ৳{balance_after:.2f}"
            )
        elif event_type == "transfer_in":
            message = (
                f"Received ৳{amount:.2f} from account {data.get('source_account', 'N/A')}. "
                f"Balance: ৳{balance_after:.2f}"
            )
        elif event_type == "login":
            message = f"Login detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        elif event_type == "login_failed":
            message = "Failed login attempt detected on your account."
        else:
            message = f"Transaction event: {event_type}"

        self.db_manager.execute(
            "INSERT INTO notifications (user_id, message) VALUES (?, ?)",
            (user_id, message),
        )
        self.db_manager.commit()


class AuditLogObserver(TransactionObserver):
    """
    Observer that records all transaction events in an audit log
    for security and compliance purposes.
    """

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def update(self, event_type, data):
        """Write an entry to the audit log."""
        user_id = data.get("user_id")
        details = (
            f"Type: {event_type}, "
            f"Amount: {data.get('amount', 'N/A')}, "
            f"Account: {data.get('account_id', 'N/A')}, "
            f"Status: {data.get('status', 'completed')}"
        )

        self.db_manager.execute(
            """INSERT INTO audit_log (user_id, action, details)
               VALUES (?, ?, ?)""",
            (user_id, event_type, details),
        )
        self.db_manager.commit()


class TransactionEventManager:
    """
    Subject/Publisher that manages observer subscriptions and
    broadcasts transaction events to all registered observers.
    """

    def __init__(self):
        self._observers = {}

    def subscribe(self, event_type, observer: TransactionObserver):
        """Register an observer for a specific event type."""
        if event_type not in self._observers:
            self._observers[event_type] = []
        if observer not in self._observers[event_type]:
            self._observers[event_type].append(observer)

    def unsubscribe(self, event_type, observer: TransactionObserver):
        """Remove an observer from a specific event type."""
        if event_type in self._observers:
            self._observers[event_type] = [
                o for o in self._observers[event_type] if o is not observer
            ]

    def notify(self, event_type, data):
        """Notify all observers subscribed to the given event type."""
        observers = self._observers.get(event_type, [])
        for observer in observers:
            observer.update(event_type, data)

    def subscribe_all(self, observer: TransactionObserver):
        """Subscribe an observer to all standard event types."""
        for event_type in [
            "withdrawal", "deposit", "transfer", "transfer_in",
            "login", "login_failed",
        ]:
            self.subscribe(event_type, observer)
