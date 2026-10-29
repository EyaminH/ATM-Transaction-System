"""
ATM Transaction System — Flask Application
============================================
Main entry point that wires together all services, design patterns,
and routes. Seeds demo data on first run.
"""
from flask import Flask
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

from atm_system.routes.auth_routes import auth_bp
from atm_system.routes.account_routes import account_bp
from atm_system.routes.transaction_routes import transaction_bp
from atm_system.routes.history_routes import history_bp
from atm_system.routes.admin_routes import admin_bp
from flask_swagger_ui import get_swaggerui_blueprint


def create_app(config_class=Config):
    """Application factory — creates and configures the Flask app."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config.from_object(config_class)

    # ── Database (Singleton pattern) ──────────────────────────
    db_manager = DatabaseManager(config_class.DATABASE_PATH)
    db_manager.db_path = config_class.DATABASE_PATH
    db_manager.init_db()

    # ── Observer pattern — event manager with observers ───────
    event_manager = TransactionEventManager()
    notification_observer = NotificationObserver(db_manager)
    audit_observer = AuditLogObserver(db_manager)
    event_manager.subscribe_all(notification_observer)
    event_manager.subscribe_all(audit_observer)

    # ── Services (injected into app config for routes) ────────
    auth_service = AuthService(db_manager, config_class, event_manager)
    account_service = AccountService(db_manager)
    transaction_service = TransactionService(
        db_manager, config_class, event_manager
    )
    history_service = HistoryService(db_manager)
    admin_service = AdminService(db_manager)

    app.config["DB_MANAGER"] = db_manager
    app.config["AUTH_SERVICE"] = auth_service
    app.config["ACCOUNT_SERVICE"] = account_service
    app.config["TRANSACTION_SERVICE"] = transaction_service
    app.config["HISTORY_SERVICE"] = history_service
    app.config["ADMIN_SERVICE"] = admin_service
    app.config["EVENT_MANAGER"] = event_manager

    # ── Register blueprints ───────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_bp)

    # ── Swagger UI (API Documentation) ────────────────────────
    swagger_ui_bp = get_swaggerui_blueprint(
        "/api/docs",
        "/static/swagger.json",
        config={"app_name": "ATM System API Documentation"},
    )
    app.register_blueprint(swagger_ui_bp, url_prefix="/api/docs")

    # ── Seed demo data on first run ───────────────────────────
    _seed_demo_data(auth_service, account_service, db_manager)

    return app


def _seed_demo_data(auth_service, account_service, db_manager):
    """Insert demo users and accounts if the database is empty."""
    existing = db_manager.execute("SELECT COUNT(*) as c FROM users").fetchone()
    if existing["c"] > 0:
        return

    # Admin user
    success, admin = auth_service.register_user(
        card_number="1111222233334444",
        pin="1234",
        full_name="Admin User",
        email="admin@atm.com",
        phone="01700000000",
        is_admin=1,
    )
    if success:
        account_service.create_account(
            admin["id"], "savings", 500000.0
        )

    # Regular user 1
    success, user1 = auth_service.register_user(
        card_number="5555666677778888",
        pin="5678",
        full_name="Rahim Uddin",
        email="rahim@email.com",
        phone="01711111111",
    )
    if success:
        account_service.create_account(
            user1["id"], "savings", 25000.0
        )
        account_service.create_account(
            user1["id"], "current", 50000.0
        )

    # Regular user 2
    success, user2 = auth_service.register_user(
        card_number="9999000011112222",
        pin="4321",
        full_name="Fatima Akter",
        email="fatima@email.com",
        phone="01722222222",
    )
    if success:
        account_service.create_account(
            user2["id"], "savings", 75000.0
        )


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
