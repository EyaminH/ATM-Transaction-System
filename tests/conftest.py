"""Test configuration and shared fixtures for ATM system tests."""
import os
import pytest
from atm_system.config import Config
from atm_system.patterns.singleton import DatabaseManager
from atm_system.patterns.observer import (
    TransactionEventManager,
    NotificationObserver,
    AuditLogObserver,
)
from atm_system.services.auth_service import AuthService
from atm_system.services.account_service import AccountService
from atm_system.services.transaction_service import TransactionService
from atm_system.services.history_service import HistoryService
from atm_system.services.admin_service import AdminService
from atm_system.app import create_app


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key-atm"
    MAX_LOGIN_ATTEMPTS = 3
    DAILY_WITHDRAWAL_LIMIT = 50000.0
    PER_TRANSACTION_LIMIT = 20000.0


@pytest.fixture(autouse=True)
def cleanup_singleton():
    """Ensure singleton DB manager is reset before and after every test."""
    DatabaseManager.reset_instance()
    yield
    DatabaseManager.reset_instance()


@pytest.fixture
def test_db_path(tmp_path):
    """Temporary SQLite database file path."""
    db_file = tmp_path / "test_atm.db"
    return str(db_file)


@pytest.fixture
def test_db(test_db_path):
    """Initialize test database with tables."""
    DatabaseManager.reset_instance()
    db = DatabaseManager(test_db_path)
    db.init_db()
    yield db
    db.close()
    DatabaseManager.reset_instance()


@pytest.fixture
def event_manager(test_db):
    """Event manager with attached notification and audit log observers."""
    em = TransactionEventManager()
    em.subscribe_all(NotificationObserver(test_db))
    em.subscribe_all(AuditLogObserver(test_db))
    return em


@pytest.fixture
def auth_service(test_db, event_manager):
    return AuthService(test_db, TestConfig, event_manager)


@pytest.fixture
def account_service(test_db):
    return AccountService(test_db)


@pytest.fixture
def transaction_service(test_db, event_manager):
    return TransactionService(test_db, TestConfig, event_manager)


@pytest.fixture
def history_service(test_db):
    return HistoryService(test_db)


@pytest.fixture
def admin_service(test_db):
    return AdminService(test_db)


@pytest.fixture
def sample_user(auth_service, account_service):
    """Create a regular sample user with a savings account."""
    success, user = auth_service.register_user(
        card_number="1234567812345678",
        pin="1234",
        full_name="Alice Wonder",
        email="alice@test.com",
        phone="01711223344",
        is_admin=0,
    )
    acc = account_service.create_account(user["id"], "savings", 10000.0)
    return {"user": user, "account": acc}


@pytest.fixture
def sample_admin(auth_service, account_service):
    """Create an admin user with an account."""
    success, admin = auth_service.register_user(
        card_number="8888777766665555",
        pin="9999",
        full_name="Admin Boss",
        email="admin@test.com",
        phone="01799887766",
        is_admin=1,
    )
    acc = account_service.create_account(admin["id"], "savings", 250000.0)
    return {"user": admin, "account": acc}


@pytest.fixture
def app(test_db_path):
    """Flask application initialized with TestConfig."""
    DatabaseManager.reset_instance()

    class DynamicTestConfig(TestConfig):
        DATABASE_PATH = test_db_path

    app_instance = create_app(DynamicTestConfig)
    return app_instance


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()
