"""
Adapter Pattern (Structural)
=============================
Problem it solves:
    The ATM system needs to communicate with external inter-bank switching
    networks (e.g., Bangladesh Bank NPSB / BEFTN / VISA Network). These external
    systems have legacy, proprietary APIs with incompatible signatures and
    payload structures.
    The Adapter pattern converts the incompatible interface of the external
    banking switch into the standard `PaymentGateway` target interface expected
    by our ATM system without modifying either system's core codebase.

Alternative rejected:
    Direct tight coupling — embedding the external vendor's specific SDK
    calls throughout the transaction service. This was rejected because if the
    bank switches from NPSB to another clearing network, every transaction
    class would need to be rewritten, violating the Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    """Target interface expected by the ATM Transaction System."""

    @abstractmethod
    def process_payment(self, source_account: str, destination_account: str, amount: float) -> dict:
        """Standardized inter-bank transaction interface."""
        pass

    @abstractmethod
    def verify_account(self, account_number: str) -> bool:
        """Standardized account verification interface."""
        pass


class LegacyNationalPaymentSwitch:
    """
    Adaptee: Simulates a legacy 3rd-party banking switch (e.g., NPSB)
    with a completely different, incompatible XML-like / key-value protocol.
    """

    def transmit_settlement(self, sender_acc: str, receiver_acc: str, amt_bdt: int, ref_code: str) -> str:
        """Legacy method expecting integer amounts in cents or exact BDT and returns raw text response."""
        if amt_bdt <= 0:
            return "STATUS=REJECTED;CODE=ERR_INVALID_AMT"
        return f"STATUS=SETTLED;TXID=SW-{ref_code};CODE=SUCCESS"

    def query_bin_directory(self, acc_num: str) -> str:
        """Legacy account lookup returning key-value string."""
        if acc_num and len(acc_num) == 10:
            return "STATUS=VALID;INSTITUTION=ROUTING_SUCCESS"
        return "STATUS=INVALID;INSTITUTION=UNKNOWN"


class BankPaymentSwitchAdapter(PaymentGateway):
    """
    Adapter: Converts LegacyNationalPaymentSwitch interface to PaymentGateway.
    """

    def __init__(self, adaptee: LegacyNationalPaymentSwitch):
        self._adaptee = adaptee

    def process_payment(self, source_account: str, destination_account: str, amount: float) -> dict:
        """Adapts process_payment call to transmit_settlement."""
        import uuid
        ref_code = str(uuid.uuid4())[:8].upper()
        amt_int = int(amount)

        raw_response = self._adaptee.transmit_settlement(
            sender_acc=source_account,
            receiver_acc=destination_account,
            amt_bdt=amt_int,
            ref_code=ref_code,
        )

        success = "STATUS=SETTLED" in raw_response
        return {
            "success": success,
            "reference_id": f"SW-{ref_code}" if success else None,
            "raw_response": raw_response,
            "message": "External settlement successful" if success else "External settlement rejected",
        }

    def verify_account(self, account_number: str) -> bool:
        """Adapts verify_account call to query_bin_directory."""
        raw_response = self._adaptee.query_bin_directory(account_number)
        return "STATUS=VALID" in raw_response
