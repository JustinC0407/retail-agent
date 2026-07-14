

import json
from typing import Any, Dict
from src.envs.tool import Tool
from src.envs.retail.tools.types import PaymentRecord, TransactionType


class ModifyPendingOrderPayment(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        order_id: str,
        payment_method_id: str,
    ) -> str:
        """
        Modify the payment method of a pending order.

        Args:
            data: The shared database dict with "orders" and "users" keys.
            order_id: The order ID (e.g. "#W0000000").
            payment_method_id: The new payment method ID to charge.

        Returns:
            json.dumps(order) with the updated order on success, or an error
            string on failure.
        """

        # Check order exists and is pending
        orders, users = data["orders"], data["users"]
        if order_id not in orders:
            return "Error: order not found"
        order = orders[order_id]
        if order["status"] != "pending":
            return "Error: non-pending order cannot be modified"

        # Check new payment method belongs to this user
        user_payment_methods = users[order["user_id"]]["payment_methods"]
        if payment_method_id not in user_payment_methods:
            return "Error: payment method not found"

        # Validate payment history has exactly one payment entry
        if not (
            len(order["payment_history"]) == 1
            and order["payment_history"][0]["transaction_type"] == TransactionType.PAYMENT
        ):
            return "Error: there should be exactly one payment for a pending order"

        # Check the new payment method is different from the current one
        old_payment_method_id = order["payment_history"][0]["payment_method_id"]
        if payment_method_id == old_payment_method_id:
            return "Error: the new payment method should be different from the current one"

        # Check gift card has sufficient balance
        amount = order["payment_history"][0]["amount"]
        new_payment_method = user_payment_methods[payment_method_id]
        if new_payment_method["source"] == "gift_card" and new_payment_method["balance"] < amount:
            return "Error: insufficient gift card balance to pay for the order"

        new_records = []
        # Charge the new payment method and refund the old one for the order
        # amount, adjusting gift card balances where either method is a gift card.
        new_records.append(
            PaymentRecord(
                transaction_type=TransactionType.PAYMENT,
                amount=amount,
                payment_method_id=payment_method_id,
            )
        )
        new_records.append(
            PaymentRecord(
                transaction_type=TransactionType.REFUND,
                amount=amount,
                payment_method_id=old_payment_method_id,
            )
        )

        if new_payment_method["source"] == "gift_card":
            new_payment_method["balance"] = round(new_payment_method["balance"] - amount, 2)

        old_payment_method = user_payment_methods[old_payment_method_id]
        if old_payment_method["source"] == "gift_card":
            old_payment_method["balance"] = round(old_payment_method["balance"] + amount, 2)

        order["payment_history"].extend(r.to_dict() for r in new_records)
        return json.dumps(order)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "modify_pending_order_payment",
                "description": "Modify the payment method of a pending order. The agent needs to explain the modification detail and ask for explicit user confirmation (yes/no) to proceed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.",
                        },
                        "payment_method_id": {
                            "type": "string",
                            "description": "The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.",
                        },
                    },
                    "required": [
                        "order_id",
                        "payment_method_id",
                    ],
                },
            },
        }
