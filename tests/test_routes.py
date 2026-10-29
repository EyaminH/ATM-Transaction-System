"""Integration tests for Flask routes and controllers."""
from flask import session


class TestAuthAndDashboardRoutes:
    """Verifies HTTP endpoints for authentication, session handling and dashboard."""

    def test_login_page_renders(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert b"ATM Transaction System" in response.data

    def test_swagger_docs_endpoint(self, client):
        response = client.get("/api/docs/")
        assert response.status_code == 200
        assert b"swagger" in response.data.lower()

    def test_dashboard_requires_login(self, client):
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_login_flow_success(self, client):
        # Demo user seeded in create_app: card "5555666677778888", PIN "5678"
        response = client.post("/login", data={
            "card_number": "5555666677778888",
            "pin": "5678",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Welcome, Rahim Uddin" in response.data

    def test_login_flow_invalid_credentials(self, client):
        response = client.post("/login", data={
            "card_number": "5555666677778888",
            "pin": "0000",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Incorrect PIN" in response.data

    def test_logout_clears_session(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["user_name"] = "Rahim Uddin"

        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"logged out successfully" in response.data


class TestTransactionRoutes:
    """Verifies cash operations via web endpoints."""

    def test_withdrawal_endpoint(self, client, app):
        # Log in Rahim Uddin
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})

        # Get accounts
        account_service = app.config["ACCOUNT_SERVICE"]
        accounts = account_service.get_accounts_by_user(2)
        assert len(accounts) >= 1
        acc_id = accounts[0]["id"]
        initial_balance = accounts[0]["balance"]

        # Perform withdrawal
        res = client.post("/withdraw", data={
            "account_id": acc_id,
            "amount": "1000",
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"withdrawn successfully" in res.data

        # Check balance reduced
        updated = account_service.get_account_by_id(acc_id)
        assert updated["balance"] == initial_balance - 1000.0

    def test_deposit_endpoint(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        account_service = app.config["ACCOUNT_SERVICE"]
        accounts = account_service.get_accounts_by_user(2)
        acc_id = accounts[0]["id"]
        initial_balance = accounts[0]["balance"]

        res = client.post("/deposit", data={
            "account_id": acc_id,
            "amount": "2000",
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"deposited successfully" in res.data

        updated = account_service.get_account_by_id(acc_id)
        assert updated["balance"] == initial_balance + 2000.0

    def test_deposit_hardware_sensor_flow(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        # 1. GET deposit page generates a random sensor reading
        res_get = client.get("/deposit")
        assert res_get.status_code == 200
        assert b"ATM Sensor Counted Cash" in res_get.data
        assert b"Hardware Locked" in res_get.data

        with client.session_transaction() as sess:
            sensor = sess.get("cdm_sensor_data")
            assert sensor is not None
            assert sensor["total_amount"] > 0
            counted = sensor["total_amount"]

        # 2. POST with matching amount succeeds
        account_service = app.config["ACCOUNT_SERVICE"]
        acc = account_service.get_accounts_by_user(2)[0]
        res_post = client.post("/deposit", data={
            "account_id": acc["id"],
            "amount": str(counted),
        }, follow_redirects=True)
        assert res_post.status_code == 200
        assert b"deposited successfully" in res_post.data

    def test_transfer_endpoint(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        account_service = app.config["ACCOUNT_SERVICE"]
        rahim_acc = account_service.get_accounts_by_user(2)[0]
        fatima_acc = account_service.get_accounts_by_user(3)[0]

        res = client.post("/transfer", data={
            "account_id": rahim_acc["id"],
            "target_account": fatima_acc["account_number"],
            "amount": "1500",
        }, follow_redirects=True)
        assert res.status_code == 200
        assert b"transferred successfully" in res.data


class TestHistoryAndAdminRoutes:
    """Verifies statements, notifications, and administrative access controls."""

    def test_history_and_statement_view(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        account_service = app.config["ACCOUNT_SERVICE"]
        acc_id = account_service.get_accounts_by_user(2)[0]["id"]

        history_res = client.get("/history")
        assert history_res.status_code == 200
        assert b"Transaction History" in history_res.data

        stmt_res = client.get(f"/statement/{acc_id}")
        assert stmt_res.status_code == 200
        assert b"Account Statement" in stmt_res.data

    def test_admin_route_protection_non_admin(self, client):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        response = client.get("/admin/", follow_redirects=True)
        assert b"Admin privileges required" in response.data

    def test_admin_portal_access_admin_user(self, client):
        # Admin: card "1111222233334444", PIN "1234"
        client.post("/login", data={"card_number": "1111222233334444", "pin": "1234"})
        res = client.get("/admin/")
        assert res.status_code == 200
        assert b"System Administration" in res.data

        # Check admin user list
        res_users = client.get("/admin/users")
        assert res_users.status_code == 200
        assert b"User Management" in res_users.data

        # Check admin accounts
        res_accs = client.get("/admin/accounts")
        assert res_accs.status_code == 200
        assert b"Account Registry" in res_accs.data

        # Check admin all transactions
        res_txs = client.get("/admin/transactions")
        assert res_txs.status_code == 200
        assert b"Global Transaction Log" in res_txs.data

        # Check admin audit log
        res_audit = client.get("/admin/audit")
        assert res_audit.status_code == 200
        assert b"Audit Trail" in res_audit.data

        # Admin toggle user status
        res_toggle = client.get("/admin/users/toggle/2", follow_redirects=True)
        assert res_toggle.status_code == 200
        assert b"successfully" in res_toggle.data

        # Admin unlock user
        res_unlock = client.get("/admin/users/unlock/2", follow_redirects=True)
        assert res_unlock.status_code == 200
        assert b"unlocked" in res_unlock.data

    def test_account_details_route(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        account_service = app.config["ACCOUNT_SERVICE"]
        acc = account_service.get_accounts_by_user(2)[0]

        res = client.get(f"/account/{acc['id']}")
        assert res.status_code == 200
        assert b"Account Details" in res.data

        # Account not belonging to user
        res_foreign = client.get("/account/1", follow_redirects=True)
        assert res_foreign.status_code == 200
        assert b"Account not found" in res_foreign.data

    def test_change_pin_routes(self, client):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})

        res_get = client.get("/change-pin")
        assert res_get.status_code == 200
        assert b"Change ATM PIN" in res_get.data

        # Mismatched PIN
        res_mismatch = client.post("/change-pin", data={
            "old_pin": "5678",
            "new_pin": "1234",
            "confirm_pin": "9999",
        }, follow_redirects=True)
        assert b"do not match" in res_mismatch.data

        # Successful change
        res_ok = client.post("/change-pin", data={
            "old_pin": "5678",
            "new_pin": "4321",
            "confirm_pin": "4321",
        }, follow_redirects=True)
        assert b"successfully" in res_ok.data

    def test_notifications_route_and_read_actions(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        db = app.config["DB_MANAGER"]
        db.execute("INSERT INTO notifications (user_id, message, is_read) VALUES (2, 'Test notification', 0)")
        db.commit()
        notif_id = db.execute("SELECT id FROM notifications WHERE user_id = 2").fetchone()["id"]

        res = client.get("/notifications")
        assert res.status_code == 200
        assert b"Notifications" in res.data

        res_read = client.get(f"/notifications/read/{notif_id}", follow_redirects=True)
        assert res_read.status_code == 200

        res_read_all = client.get("/notifications/read-all", follow_redirects=True)
        assert res_read_all.status_code == 200
        assert b"marked as read" in res_read_all.data

    def test_transaction_form_errors(self, client, app):
        client.post("/login", data={"card_number": "5555666677778888", "pin": "5678"})
        account_service = app.config["ACCOUNT_SERVICE"]
        acc = account_service.get_accounts_by_user(2)[0]

        # Invalid withdraw amount
        res_w_invalid = client.post("/withdraw", data={"account_id": acc["id"], "amount": "abc"})
        assert b"valid amount" in res_w_invalid.data

        # Withdraw exceeding balance
        res_w_exceed = client.post("/withdraw", data={"account_id": acc["id"], "amount": "9999999"}, follow_redirects=True)
        assert b"Insufficient" in res_w_exceed.data

        # Invalid deposit amount
        res_d_invalid = client.post("/deposit", data={"account_id": acc["id"], "amount": "invalid"})
        assert b"valid amount" in res_d_invalid.data

        # CDM physical cash slot mismatch
        res_d_mismatch = client.post("/deposit", data={
            "account_id": acc["id"],
            "amount": "5000",
            "counted_cash": "3000",
        }, follow_redirects=True)
        assert b"Cash Deposit Mismatch" in res_d_mismatch.data

        # Missing target account
        res_t_missing = client.post("/transfer", data={"account_id": acc["id"], "target_account": "", "amount": "100"})
        assert b"target account number" in res_t_missing.data

