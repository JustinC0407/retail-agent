"""
Minimal mock database for tool unit tests.
Schema mirrors the real data files in src/envs/retail/data/.
Each test imports get_fresh_data() to get an independent copy.
"""
import copy

_BASE_DATA = {
    "users": {
        "alice_smith_1000": {
            "name": {"first_name": "Alice", "last_name": "Smith"},
            "address": {"address1": "1 Main St", "address2": "", "city": "Boston",
                        "state": "MA", "country": "USA", "zip": "02101"},
            "email": "alice@example.com",
            "payment_methods": {
                "credit_card_1111": {"source": "credit_card", "brand": "visa",
                                     "last_four": "1111", "id": "credit_card_1111"},
                "gift_card_2222": {"source": "gift_card", "balance": 200.00,
                                   "id": "gift_card_2222"},
            },
            "orders": ["#W0001", "#W0002"],
        },
        "bob_jones_2000": {
            "name": {"first_name": "Bob", "last_name": "Jones"},
            "address": {"address1": "99 Oak Ave", "address2": "", "city": "Austin",
                        "state": "TX", "country": "USA", "zip": "73301"},
            "email": "bob@example.com",
            "payment_methods": {
                "credit_card_3333": {"source": "credit_card", "brand": "mastercard",
                                     "last_four": "3333", "id": "credit_card_3333"},
            },
            "orders": ["#W0003"],
        },
    },
    "orders": {
        # pending order — credit card payment, two items from PROD-1
        "#W0001": {
            "order_id": "#W0001",
            "user_id": "alice_smith_1000",
            "status": "pending",
            "items": [
                {"item_id": "ITEM-A", "product_id": "PROD-1", "price": 50.00,
                 "options": {"color": "red"}},
                {"item_id": "ITEM-B", "product_id": "PROD-1", "price": 30.00,
                 "options": {"color": "blue"}},
            ],
            "payment_history": [
                {"transaction_type": "payment", "amount": 80.00,
                 "payment_method_id": "credit_card_1111"},
            ],
            "address": {"address1": "1 Main St", "address2": "", "city": "Boston",
                        "state": "MA", "country": "USA", "zip": "02101"},
        },
        # pending order — gift card payment
        "#W0002": {
            "order_id": "#W0002",
            "user_id": "alice_smith_1000",
            "status": "pending",
            "items": [
                {"item_id": "ITEM-C", "product_id": "PROD-2", "price": 60.00,
                 "options": {}},
            ],
            "payment_history": [
                {"transaction_type": "payment", "amount": 60.00,
                 "payment_method_id": "gift_card_2222"},
            ],
            "address": {"address1": "1 Main St", "address2": "", "city": "Boston",
                        "state": "MA", "country": "USA", "zip": "02101"},
        },
        # pending order for Bob
        "#W0003": {
            "order_id": "#W0003",
            "user_id": "bob_jones_2000",
            "status": "pending",
            "items": [
                {"item_id": "ITEM-F", "product_id": "PROD-4", "price": 25.00,
                 "options": {}},
            ],
            "payment_history": [
                {"transaction_type": "payment", "amount": 25.00,
                 "payment_method_id": "credit_card_3333"},
            ],
            "address": {},
        },
    },
    "products": {
        "PROD-1": {
            "name": "Widget",
            "variants": {
                "ITEM-A": {"price": 50.00, "options": {"color": "red"},   "available": True},
                "ITEM-B": {"price": 30.00, "options": {"color": "blue"},  "available": True},
                "ITEM-G": {"price": 45.00, "options": {"color": "green"}, "available": True},
            },
        },
    },
}


def get_fresh_data() -> dict:
    """Return a deep copy of the mock database so each test is independent."""
    return copy.deepcopy(_BASE_DATA)
