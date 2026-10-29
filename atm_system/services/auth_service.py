"""
Module 1: User Authentication Service
=======================================
Handles PIN-based authentication, card validation, session management,
and account lockout after repeated failures.
"""
import hashlib
from datetime import datetime, timedelta


class AuthService:
    """Manages user authentication for the ATM system."""

    def __init__(self, db_manager, config, event_manager=None):
        self.db = db_manager
        self.config = config
        self.event_manager = event_manager

    @staticmethod
    def hash_pin(pin):
        """Hash a PIN using SHA-256 for secure storage."""
        return hashlib.sha256(str(pin).encode()).hexdigest()

    def authenticate(self, card_number, pin):
        """
        Authenticate a user by card number and PIN.
        Returns (success, user_dict | error_message).
        """
        row = self.db.execute(
            "SELECT * FROM users WHERE card_number = ?", (card_number,)
        ).fetchone()

        if row is None:
            return False, "Invalid card number."

        user = dict(row)

        # Check if account is active
        if not user["is_active"]:
            return False, "This account has been deactivated. Contact bank support."

        # Check if account is locked
        if user["locked_until"]:
            locked_until = datetime.fromisoformat(user["locked_until"])
            if datetime.now() < locked_until:
                remaining = (locked_until - datetime.now()).seconds // 60
                return False, (
                    f"Account is locked due to too many failed attempts. "
                    f"Try again in {remaining + 1} minute(s)."
                )
            else:
                # Lock period expired — reset
                self.db.execute(
                    "UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = ?",
                    (user["id"],),
                )
                self.db.commit()
                user["login_attempts"] = 0

        # Verify PIN
        if self.hash_pin(pin) != user["pin_hash"]:
            attempts = user["login_attempts"] + 1
            if attempts >= self.config.MAX_LOGIN_ATTEMPTS:
                lock_time = datetime.now() + timedelta(minutes=15)
                self.db.execute(
                    "UPDATE users SET login_attempts = ?, locked_until = ? WHERE id = ?",
                    (attempts, lock_time.isoformat(), user["id"]),
                )
                self.db.commit()
                if self.event_manager:
                    self.event_manager.notify(
                        "login_failed", {"user_id": user["id"]}
                    )
                return False, (
                    "Account locked for 15 minutes due to too many failed attempts."
                )
            else:
                self.db.execute(
                    "UPDATE users SET login_attempts = ? WHERE id = ?",
                    (attempts, user["id"]),
                )
                self.db.commit()
                remaining = self.config.MAX_LOGIN_ATTEMPTS - attempts
                if self.event_manager:
                    self.event_manager.notify(
                        "login_failed", {"user_id": user["id"]}
                    )
                return False, (
                    f"Incorrect PIN. {remaining} attempt(s) remaining."
                )

        # Successful login — reset attempts
        self.db.execute(
            "UPDATE users SET login_attempts = 0, locked_until = NULL WHERE id = ?",
            (user["id"],),
        )
        self.db.commit()

        if self.event_manager:
            self.event_manager.notify("login", {"user_id": user["id"]})

        return True, user

    def register_user(self, card_number, pin, full_name, email="", phone="", is_admin=0):
        """Register a new user in the system."""
        existing = self.db.execute(
            "SELECT id FROM users WHERE card_number = ?", (card_number,)
        ).fetchone()
        if existing:
            return False, "Card number already registered."

        if len(str(pin)) < self.config.MIN_PIN_LENGTH:
            return False, f"PIN must be at least {self.config.MIN_PIN_LENGTH} digits."

        self.db.execute(
            """INSERT INTO users (card_number, pin_hash, full_name, email, phone, is_admin)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (card_number, self.hash_pin(pin), full_name, email, phone, is_admin),
        )
        self.db.commit()

        user = self.db.execute(
            "SELECT * FROM users WHERE card_number = ?", (card_number,)
        ).fetchone()

        return True, dict(user)

    def change_pin(self, user_id, old_pin, new_pin):
        """Change a user's PIN after verifying the old one."""
        user = self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if user is None:
            return False, "User not found."

        if self.hash_pin(old_pin) != user["pin_hash"]:
            return False, "Current PIN is incorrect."

        if len(str(new_pin)) < self.config.MIN_PIN_LENGTH:
            return False, f"New PIN must be at least {self.config.MIN_PIN_LENGTH} digits."

        if old_pin == new_pin:
            return False, "New PIN must be different from the current PIN."

        self.db.execute(
            "UPDATE users SET pin_hash = ?, updated_at = datetime('now') WHERE id = ?",
            (self.hash_pin(new_pin), user_id),
        )
        self.db.commit()
        return True, "PIN changed successfully."

    def get_user_by_id(self, user_id):
        """Retrieve a user by their ID."""
        row = self.db.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
