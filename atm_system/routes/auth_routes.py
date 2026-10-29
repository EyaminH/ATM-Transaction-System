"""Authentication routes — login, logout, PIN change."""
from flask import Blueprint, request, session, redirect, url_for, render_template, flash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login."""
    if "user_id" in session:
        return redirect(url_for("account.dashboard"))

    if request.method == "POST":
        from flask import current_app
        auth_service = current_app.config["AUTH_SERVICE"]

        card_number = request.form.get("card_number", "").strip()
        pin = request.form.get("pin", "").strip()

        if not card_number or not pin:
            flash("Please enter both card number and PIN.", "error")
            return render_template("login.html")

        success, result = auth_service.authenticate(card_number, pin)
        if success:
            session["user_id"] = result["id"]
            session["user_name"] = result["full_name"]
            session["is_admin"] = result["is_admin"]
            session["card_number"] = result["card_number"]
            flash(f"Welcome, {result['full_name']}!", "success")
            return redirect(url_for("account.dashboard"))
        else:
            flash(result, "error")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Log the user out."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-pin", methods=["GET", "POST"])
def change_pin():
    """Handle PIN change."""
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        from flask import current_app
        auth_service = current_app.config["AUTH_SERVICE"]

        old_pin = request.form.get("old_pin", "").strip()
        new_pin = request.form.get("new_pin", "").strip()
        confirm_pin = request.form.get("confirm_pin", "").strip()

        if new_pin != confirm_pin:
            flash("New PIN and confirmation do not match.", "error")
            return render_template("change_pin.html")

        success, message = auth_service.change_pin(
            session["user_id"], old_pin, new_pin
        )
        if success:
            flash(message, "success")
            return redirect(url_for("account.dashboard"))
        else:
            flash(message, "error")

    return render_template("change_pin.html")
