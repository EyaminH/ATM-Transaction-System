"""Admin routes — system monitoring, user management, audit log."""
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash, current_app,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    """Decorator to restrict access to admin users."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        if not session.get("is_admin"):
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("account.dashboard"))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/")
@admin_required
def admin_dashboard():
    """Admin dashboard with system statistics."""
    admin_service = current_app.config["ADMIN_SERVICE"]
    stats = admin_service.get_system_stats()
    tx_summary = admin_service.get_transaction_summary()
    return render_template(
        "admin.html", stats=stats, tx_summary=tx_summary
    )


@admin_bp.route("/users")
@admin_required
def manage_users():
    """View and manage all users."""
    admin_service = current_app.config["ADMIN_SERVICE"]
    users = admin_service.get_all_users()
    return render_template("admin_users.html", users=users)


@admin_bp.route("/users/toggle/<int:user_id>")
@admin_required
def toggle_user(user_id):
    """Toggle user active status."""
    admin_service = current_app.config["ADMIN_SERVICE"]
    success, message = admin_service.toggle_user_status(user_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/unlock/<int:user_id>")
@admin_required
def unlock_user(user_id):
    """Unlock a locked user account."""
    admin_service = current_app.config["ADMIN_SERVICE"]
    success, message = admin_service.unlock_user(user_id)
    flash(message, "success" if success else "error")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/accounts")
@admin_required
def manage_accounts():
    """View all accounts in the system."""
    account_service = current_app.config["ACCOUNT_SERVICE"]
    accounts = account_service.get_all_accounts()
    return render_template("admin_accounts.html", accounts=accounts)


@admin_bp.route("/transactions")
@admin_required
def all_transactions():
    """View all transactions system-wide."""
    history_service = current_app.config["HISTORY_SERVICE"]
    transactions = history_service.get_all_transactions(limit=100)
    return render_template("admin_transactions.html", transactions=transactions)


@admin_bp.route("/audit")
@admin_required
def audit_log():
    """View the audit log."""
    admin_service = current_app.config["ADMIN_SERVICE"]
    logs = admin_service.get_audit_log(limit=100)
    return render_template("admin_audit.html", logs=logs)
