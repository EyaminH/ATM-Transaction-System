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


def _generate_sensor_data():
    """Simulate optical banknote scanner reading inside Cash Deposit Machine (CDM) tray."""
    import random
    possible_totals = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, 6000, 7000, 8000, 10000]
    target_total = random.choice(possible_totals)

    rem = target_total
    max_1000 = rem // 1000
    n1000 = random.randint(max(0, max_1000 - 2), max_1000)
    rem -= n1000 * 1000

    max_500 = rem // 500
    n500 = random.randint(max(0, max_500 - 1), max_500)
    rem -= n500 * 500

    max_200 = rem // 200
    n200 = random.randint(max(0, max_200 - 1), max_200)
    rem -= n200 * 200

    n100 = rem // 100
    rem -= n100 * 100

    return {
        "n1000": n1000,
        "n500": n500,
        "n200": n200,
        "n100": n100,
        "total_amount": float(target_total),
    }


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
        sensor_data = session.get("cdm_sensor_data")

        try:
            amount = float(request.form.get("amount", 0))
        except ValueError:
            flash("Please enter a valid amount.", "error")
            if not sensor_data:
                sensor_data = _generate_sensor_data()
            return render_template("deposit.html", accounts=accounts, sensor=sensor_data)

        # Retrieve hardware counted cash from secure session or form fallback
        if sensor_data and "total_amount" in sensor_data:
            counted_cash = float(sensor_data["total_amount"])
        elif request.form.get("counted_cash"):
            try:
                counted_cash = float(request.form.get("counted_cash"))
            except ValueError:
                counted_cash = None
        else:
            # Direct API/test POST without prior GET or tray simulation
            counted_cash = amount
            sensor_data = {
                "n1000": int(amount) // 1000,
                "n500": (int(amount) % 1000) // 500,
                "n200": (int(amount) % 500) // 200,
                "n100": (int(amount) % 200) // 100,
                "total_amount": amount,
            }

        result = transaction_service.deposit(
            account_id, amount, user_id=session["user_id"], counted_cash=counted_cash
        )
        if result["success"]:
            session.pop("cdm_sensor_data", None)
            flash(result["message"], "success")
            return redirect(url_for("account.dashboard"))
        else:
            for error in result["errors"]:
                flash(error, "error")
            return render_template("deposit.html", accounts=accounts, sensor=sensor_data)

    # GET Request: ALWAYS generate a fresh random banknote sensor count every time user visits
    sensor_data = _generate_sensor_data()
    session["cdm_sensor_data"] = sensor_data

    return render_template("deposit.html", accounts=accounts, sensor=sensor_data)


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
