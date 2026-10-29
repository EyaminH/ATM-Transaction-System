"""
Configuration module for the ATM Transaction System.
Contains all application settings and constants.
"""
import os


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "atm-secret-key-dev-2024")
    DATABASE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "atm_system.db"
    )
    SESSION_TIMEOUT_MINUTES = 5
    MAX_LOGIN_ATTEMPTS = 3
    MIN_PIN_LENGTH = 4
    MAX_WITHDRAWAL_AMOUNT = 50000.00
    MIN_WITHDRAWAL_AMOUNT = 100.00
    MIN_DEPOSIT_AMOUNT = 100.00
    MIN_BALANCE = 500.00  # Minimum balance to maintain
    # Resolved merge conflict: Reconciled Policy A (150k) and Policy B (80k) to balanced default limit 100k
    DAILY_WITHDRAWAL_LIMIT = 100000.00
    TRANSACTION_TYPES = ["withdrawal", "deposit", "transfer"]


class TestConfig(Config):
    """Test configuration — uses in-memory database."""
    DATABASE_PATH = ":memory:"
    TESTING = True


class ProductionConfig(Config):
    """Production configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production")
