"""Unit tests for AuthService (Authentication, Lockout, PIN change)."""
from tests.conftest import TestConfig


class TestAuthService:
    """Verifies user registration, card authentication, lockout policy and PIN change."""

    def test_register_user_success(self, auth_service):
        success, user = auth_service.register_user(
            card_number="1111000011110000",
            pin="1234",
            full_name="John Doe",
            email="john@example.com",
            phone="01700000000",
        )
        assert success is True
        assert user["card_number"] == "1111000011110000"
        assert user["full_name"] == "John Doe"

    def test_register_duplicate_card_fails(self, auth_service):
        auth_service.register_user("2222000022220000", "1234", "User 1")
        success, err = auth_service.register_user("2222000022220000", "5678", "User 2")
        assert success is False
        assert "already registered" in err

    def test_register_short_pin_fails(self, auth_service):
        success, err = auth_service.register_user("3333000033330000", "12", "User 3")
        assert success is False
        assert f"at least {TestConfig.MIN_PIN_LENGTH}" in err

    def test_authenticate_success(self, auth_service, sample_user):
        card = sample_user["user"]["card_number"]
        success, user = auth_service.authenticate(card, "1234")
        assert success is True
        assert user["id"] == sample_user["user"]["id"]

    def test_authenticate_invalid_card(self, auth_service):
        success, err = auth_service.authenticate("9999999999999999", "1234")
        assert success is False
        assert "Invalid card number" in err

    def test_authenticate_incorrect_pin_and_lockout(self, auth_service, sample_user):
        card = sample_user["user"]["card_number"]

        # Attempt 1
        success, msg = auth_service.authenticate(card, "0000")
        assert success is False
        assert "attempt(s) remaining" in msg

        # Attempt 2
        success, msg = auth_service.authenticate(card, "0000")
        assert success is False

        # Attempt 3 - Max attempts reached -> Locked
        success, msg = auth_service.authenticate(card, "0000")
        assert success is False
        assert "Account locked" in msg

        # Attempt after lock
        success, msg = auth_service.authenticate(card, "1234")
        assert success is False
        assert "Account is locked" in msg

    def test_change_pin_success(self, auth_service, sample_user):
        user_id = sample_user["user"]["id"]
        card = sample_user["user"]["card_number"]

        success, msg = auth_service.change_pin(user_id, "1234", "4321")
        assert success is True
        assert "successfully" in msg

        # New PIN should authenticate, old PIN should fail
        old_auth, _ = auth_service.authenticate(card, "1234")
        new_auth, _ = auth_service.authenticate(card, "4321")
        assert old_auth is False
        assert new_auth is True

    def test_change_pin_validation_failures(self, auth_service, sample_user):
        user_id = sample_user["user"]["id"]

        # Incorrect current PIN
        success, err = auth_service.change_pin(user_id, "9999", "5678")
        assert success is False
        assert "Current PIN is incorrect" in err

        # Same PIN
        success, err = auth_service.change_pin(user_id, "1234", "1234")
        assert success is False
        assert "different from the current PIN" in err

        # Short PIN
        success, err = auth_service.change_pin(user_id, "1234", "12")
        assert success is False
        assert "at least" in err
