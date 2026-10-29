"""Unit tests for AccountService (Account Creation, Retrieval, Activation)."""


class TestAccountService:
    """Verifies account lifecycle and status manipulation."""

    def test_create_account(self, account_service, sample_user):
        user_id = sample_user["user"]["id"]
        acc = account_service.create_account(user_id, "current", 15000.0)
        assert acc["user_id"] == user_id
        assert acc["account_type"] == "current"
        assert acc["balance"] == 15000.0
        assert len(acc["account_number"]) == 10
        assert acc["account_number"].isdigit()

    def test_get_account_by_id(self, account_service, sample_user):
        acc = sample_user["account"]
        fetched = account_service.get_account_by_id(acc["id"])
        assert fetched["account_number"] == acc["account_number"]
        assert fetched["balance"] == acc["balance"]

    def test_get_account_by_number(self, account_service, sample_user):
        acc = sample_user["account"]
        fetched = account_service.get_account_by_number(acc["account_number"])
        assert fetched["id"] == acc["id"]

    def test_get_accounts_by_user(self, account_service, sample_user):
        user_id = sample_user["user"]["id"]
        account_service.create_account(user_id, "current", 500.0)
        user_accounts = account_service.get_accounts_by_user(user_id)
        assert len(user_accounts) == 2

    def test_get_balance(self, account_service, sample_user):
        acc = sample_user["account"]
        balance = account_service.get_balance(acc["id"])
        assert balance == 10000.0
        assert account_service.get_balance(99999) is None

    def test_deactivate_and_activate_account(self, account_service, sample_user):
        acc = sample_user["account"]
        account_service.deactivate_account(acc["id"])
        assert account_service.get_account_by_id(acc["id"])["is_active"] == 0

        account_service.activate_account(acc["id"])
        assert account_service.get_account_by_id(acc["id"])["is_active"] == 1
