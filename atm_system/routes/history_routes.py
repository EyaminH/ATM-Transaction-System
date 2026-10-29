"""History routes — transaction history, statements, notifications."""
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash, current_app,
)

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
@history_bp.route("/history/<int:account_id>")
def transaction_history(account_id=None):
    """View transaction history."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    history_service = current_app.config["HISTORY_SERVICE"]
    accounts = account_service.get_accounts_by_user(session["user_id"])

    if not accounts:
        flash("No accounts found.", "error")
        return redirect(url_for("account.dashboard"))

    if account_id is None:
        account_id = accounts[0]["id"]

    # Verify account belongs to user
    account = account_service.get_account_by_id(account_id)
    if not account or account["user_id"] != session["user_id"]:
        flash("Account not found.", "error")
        return redirect(url_for("account.dashboard"))

    # Apply filters
    tx_type = request.args.get("type", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    if start_date and end_date:
        transactions = history_service.get_transactions_by_date_range(
            account_id, start_date, end_date
        )
    elif tx_type:
        transactions = history_service.get_transactions_by_type(
            account_id, tx_type
        )
    else:
        transactions = history_service.get_recent_transactions(
            account_id, limit=50
        )

    return render_template(
        "history.html",
        accounts=accounts,
        current_account_id=account_id,
        transactions=transactions,
        tx_type=tx_type,
        start_date=start_date,
        end_date=end_date,
    )


@history_bp.route("/statement/<int:account_id>")
def statement(account_id):
    """Generate a mini-statement."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    history_service = current_app.config["HISTORY_SERVICE"]

    account = account_service.get_account_by_id(account_id)
    if not account or account["user_id"] != session["user_id"]:
        flash("Account not found.", "error")
        return redirect(url_for("account.dashboard"))

    days = int(request.args.get("days", 30))
    stmt = history_service.get_statement(account_id, days=days)

    return render_template(
        "statement.html", statement=stmt, account=account, days=days
    )


@history_bp.route("/notifications")
def notifications():
    """View user notifications."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    history_service = current_app.config["HISTORY_SERVICE"]
    notifs = history_service.get_notifications(session["user_id"])

    return render_template("notifications.html", notifications=notifs)


@history_bp.route("/notifications/read/<int:notification_id>")
def mark_read(notification_id):
    """Mark a notification as read."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    history_service = current_app.config["HISTORY_SERVICE"]
    history_service.mark_notification_read(notification_id)
    return redirect(url_for("history.notifications"))


@history_bp.route("/notifications/read-all")
def mark_all_read():
    """Mark all notifications as read."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    history_service = current_app.config["HISTORY_SERVICE"]
    history_service.mark_all_notifications_read(session["user_id"])
    flash("All notifications marked as read.", "info")
    return redirect(url_for("history.notifications"))
