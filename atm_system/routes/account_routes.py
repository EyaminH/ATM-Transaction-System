"""Account routes — dashboard, balance inquiry, account details."""
from flask import Blueprint, session, redirect, url_for, render_template, flash, current_app

account_bp = Blueprint("account", __name__)


@account_bp.route("/dashboard")
def dashboard():
    """Main dashboard after login."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    history_service = current_app.config["HISTORY_SERVICE"]

    accounts = account_service.get_accounts_by_user(session["user_id"])

    # Get recent transactions for the first account
    recent_transactions = []
    if accounts:
        recent_transactions = history_service.get_recent_transactions(
            accounts[0]["id"], limit=5
        )

    # Get unread notifications count
    notifications = history_service.get_notifications(
        session["user_id"], unread_only=True
    )

    return render_template(
        "dashboard.html",
        accounts=accounts,
        recent_transactions=recent_transactions,
        notification_count=len(notifications),
    )


@account_bp.route("/account/<int:account_id>")
def account_details(account_id):
    """View details for a specific account."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    account = account_service.get_account_by_id(account_id)

    if not account or account["user_id"] != session["user_id"]:
        flash("Account not found.", "error")
        return redirect(url_for("account.dashboard"))

    return render_template("account_details.html", account=account)
