"""Unit tests for Adapter Design Pattern (Structural Pattern)."""
from unittest.mock import MagicMock
from atm_system.patterns.adapter import (
    PaymentGateway,
    LegacyNationalPaymentSwitch,
    BankPaymentSwitchAdapter,
)


class TestAdapterPattern:
    """Verifies that the Adapter correctly bridges incompatible legacy protocols."""

    def test_adapter_implements_target_interface(self):
        adaptee = LegacyNationalPaymentSwitch()
        adapter = BankPaymentSwitchAdapter(adaptee)
        assert isinstance(adapter, PaymentGateway)

    def test_adapter_successful_payment_settlement(self):
        adaptee = LegacyNationalPaymentSwitch()
        adapter = BankPaymentSwitchAdapter(adaptee)

        result = adapter.process_payment("1234567890", "0987654321", 5000.0)
        assert result["success"] is True
        assert result["reference_id"].startswith("SW-")
        assert "SETTLED" in result["raw_response"]

    def test_adapter_handles_rejections(self):
        adaptee = LegacyNationalPaymentSwitch()
        adapter = BankPaymentSwitchAdapter(adaptee)

        result = adapter.process_payment("1234567890", "0987654321", -50.0)
        assert result["success"] is False
        assert result["reference_id"] is None
        assert "ERR_INVALID_AMT" in result["raw_response"]

    def test_adapter_verify_account(self):
        adaptee = LegacyNationalPaymentSwitch()
        adapter = BankPaymentSwitchAdapter(adaptee)

        assert adapter.verify_account("1234567890") is True
        assert adapter.verify_account("123") is False

    def test_mocking_legacy_adaptee_with_mock(self):
        """Demonstrates mocking the external legacy adaptee."""
        mock_legacy = MagicMock(spec=LegacyNationalPaymentSwitch)
        mock_legacy.transmit_settlement.return_value = "STATUS=SETTLED;TXID=SW-MOCK1234;CODE=SUCCESS"

        adapter = BankPaymentSwitchAdapter(mock_legacy)
        res = adapter.process_payment("1111111111", "2222222222", 1000.0)

        assert res["success"] is True
        assert mock_legacy.transmit_settlement.called
