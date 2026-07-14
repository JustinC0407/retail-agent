from dataclasses import dataclass
from enum import Enum


class TransactionType(str, Enum):
    PAYMENT = "payment"
    REFUND = "refund"


@dataclass
class PaymentRecord:
    transaction_type: TransactionType  # "payment" or "refund"
    amount: float                      # positive dollar amount, rounded to 2 decimal places
    payment_method_id: str             # e.g. "gift_card_0000000", "credit_card_0000000", "paypal_0000000"

    def to_dict(self) -> dict:
        return {
            "transaction_type": self.transaction_type.value,
            "amount": self.amount,
            "payment_method_id": self.payment_method_id,
        }
