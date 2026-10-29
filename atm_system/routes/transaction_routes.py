"""Transaction routes — withdraw, deposit, transfer."""
from flask import (
    Blueprint, request, session, redirect, url_for,
    render_template, flash, current_app,
)

transaction_bp = Blueprint("transaction", __name__)


@transaction_bp.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    """Handle cash withdrawal."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    accounts = account_service.get_accounts_by_user(session["user_id"])

    if request.method == "POST":
        transaction_service = current_app.config["TRANSACTION_SERVICE"]
        account_id = int(request.form.get("account_id", 0))
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Please enter a valid amount.", "error")
            return render_template("withdraw.html", accounts=accounts)

        result = transaction_service.withdraw(
            account_id, amount, user_id=session["user_id"]
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("account.dashboard"))
        else:
            for error in result["errors"]:
                flash(error, "error")

    return render_template("withdraw.html", accounts=accounts)


@transaction_bp.route("/deposit", methods=["GET", "POST"])
def deposit():
    """Handle cash deposit."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    accounts = account_service.get_accounts_by_user(session["user_id"])

    if request.method == "POST":
        transaction_service = current_app.config["TRANSACTION_SERVICE"]
        account_id = int(request.form.get("account_id", 0))
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Please enter a valid amount.", "error")
            return render_template("deposit.html", accounts=accounts)

        counted_cash_str = request.form.get("counted_cash", "").strip()
        try:
            counted_cash = float(counted_cash_str) if counted_cash_str else None
        except ValueError:
            counted_cash = None

        result = transaction_service.deposit(
            account_id, amount, user_id=session["user_id"], counted_cash=counted_cash
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("account.dashboard"))
        else:
            for error in result["errors"]:
                flash(error, "error")

    return render_template("deposit.html", accounts=accounts)


@transaction_bp.route("/transfer", methods=["GET", "POST"])
def transfer():
    """Handle fund transfer."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    account_service = current_app.config["ACCOUNT_SERVICE"]
    accounts = account_service.get_accounts_by_user(session["user_id"])

    if request.method == "POST":
        transaction_service = current_app.config["TRANSACTION_SERVICE"]
        account_id = int(request.form.get("account_id", 0))
        target_account_number = request.form.get("target_account", "").strip()
        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Please enter a valid amount.", "error")
            return render_template("transfer.html", accounts=accounts)

        if not target_account_number:
            flash("Please enter the target account number.", "error")
            return render_template("transfer.html", accounts=accounts)

        result = transaction_service.transfer(
            account_id, target_account_number, amount,
            user_id=session["user_id"],
        )
        if result["success"]:
            flash(result["message"], "success")
            return redirect(url_for("account.dashboard"))
        else:
            for error in result["errors"]:
                flash(error, "error")

    return render_template("transfer.html", accounts=accounts)
