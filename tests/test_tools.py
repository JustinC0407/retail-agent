"""
Sanity-check tests for the core tool implementations.
Run from the repository root:
    pytest tests/test_tools.py -v
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from tests.mock_data import get_fresh_data

from src.envs.retail.tools.find_user_id_by_name_zip import FindUserIdByNameZip
from src.envs.retail.tools.cancel_pending_order import CancelPendingOrder
from src.envs.retail.tools.modify_pending_order_payment import ModifyPendingOrderPayment
from src.envs.retail.tools.modify_pending_order_items import ModifyPendingOrderItems


# ── find_user_id_by_name_zip ─────────────────────────────────────────────────

def test_find_user_found():
    """Returns the correct user_id when name and zip match (case-insensitive)."""
    data = get_fresh_data()
    result = FindUserIdByNameZip.invoke(data, "alice", "SMITH", "02101")
    assert result == "alice_smith_1000"


def test_find_user_not_found():
    """Returns an error string when no user matches."""
    data = get_fresh_data()
    result = FindUserIdByNameZip.invoke(data, "Charlie", "Brown", "99999")
    assert result == "Error: user not found"


# ── cancel_pending_order ─────────────────────────────────────────────────────

def test_cancel_sets_status_and_refund():
    """Cancelling a credit-card order sets status to 'cancelled' and appends a refund."""
    data = get_fresh_data()
    result = CancelPendingOrder.invoke(data, "#W0001", "no longer needed")
    order = json.loads(result)
    assert order["status"] == "cancelled"
    assert order["cancel_reason"] == "no longer needed"
    refunds = [p for p in order["payment_history"] if p["transaction_type"] == "refund"]
    assert len(refunds) == 1
    assert refunds[0]["amount"] == 80.00


def test_cancel_gift_card_restores_balance():
    """Cancelling a gift-card order immediately restores the gift card balance."""
    data = get_fresh_data()
    before = data["users"]["alice_smith_1000"]["payment_methods"]["gift_card_2222"]["balance"]
    CancelPendingOrder.invoke(data, "#W0002", "ordered by mistake")
    after = data["users"]["alice_smith_1000"]["payment_methods"]["gift_card_2222"]["balance"]
    assert round(after - before, 2) == 60.00


# ── modify_pending_order_payment ─────────────────────────────────────────────

def test_modify_payment_appends_records():
    """Switching payment method appends one payment and one refund entry."""
    data = get_fresh_data()
    result = ModifyPendingOrderPayment.invoke(data, "#W0001", "gift_card_2222")
    order = json.loads(result)
    new_payments = [p for p in order["payment_history"] if p["transaction_type"] == "payment"]
    new_refunds  = [p for p in order["payment_history"] if p["transaction_type"] == "refund"]
    assert len(new_payments) == 2  # original + new
    assert len(new_refunds)  == 1
    assert new_payments[-1]["payment_method_id"] == "gift_card_2222"


def test_modify_payment_gift_card_deducted():
    """When the new payment method is a gift card, its balance is decremented."""
    data = get_fresh_data()
    before = data["users"]["alice_smith_1000"]["payment_methods"]["gift_card_2222"]["balance"]
    ModifyPendingOrderPayment.invoke(data, "#W0001", "gift_card_2222")
    after = data["users"]["alice_smith_1000"]["payment_methods"]["gift_card_2222"]["balance"]
    assert round(before - after, 2) == 80.00


# ── modify_pending_order_items ───────────────────────────────────────────────

def test_modify_items_updates_item_and_status():
    """Swapping ITEM-A for ITEM-G updates the item and sets status to 'pending (item modified)'."""
    data = get_fresh_data()
    result = ModifyPendingOrderItems.invoke(
        data, "#W0001", ["ITEM-A"], ["ITEM-G"], "credit_card_1111"
    )
    order = json.loads(result)
    assert order["status"] == "pending (item modified)"
    item_ids = [item["item_id"] for item in order["items"]]
    assert "ITEM-G" in item_ids
    assert "ITEM-A" not in item_ids


def test_modify_items_payment_history_updated():
    """ITEM-A ($50) → ITEM-G ($45): a refund entry of $5 is appended to payment_history."""
    data = get_fresh_data()
    result = ModifyPendingOrderItems.invoke(
        data, "#W0001", ["ITEM-A"], ["ITEM-G"], "credit_card_1111"
    )
    order = json.loads(result)
    new_entry = order["payment_history"][-1]
    assert new_entry["transaction_type"] == "refund"
    assert round(new_entry["amount"], 2) == 5.00
