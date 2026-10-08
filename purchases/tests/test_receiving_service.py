
from datetime import timedelta
from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone

from purchases.services import (
    StockReceivingError,
    _positive_integer,
    _expiry_date,
    receive_purchase_stock,
)


# ============================================================
# PHASE 7.8.7.2 — STOCK RECEIVING SAFETY TESTS
# ============================================================


class PositiveIntegerValidationTests(TestCase):

    def test_accepts_positive_integer(self):
        self.assertEqual(
            _positive_integer(5, "Quantity"),
            5,
        )

    def test_accepts_positive_integer_string(self):
        self.assertEqual(
            _positive_integer("10", "Quantity"),
            10,
        )

    def test_rejects_zero(self):
        with self.assertRaises(StockReceivingError):
            _positive_integer(0, "Quantity")

    def test_rejects_negative_number(self):
        with self.assertRaises(StockReceivingError):
            _positive_integer(-5, "Quantity")

    def test_rejects_decimal_quantity(self):
        with self.assertRaises(StockReceivingError):
            _positive_integer("2.5", "Quantity")

    def test_rejects_boolean(self):
        with self.assertRaises(StockReceivingError):
            _positive_integer(True, "Quantity")

    def test_rejects_invalid_string(self):
        with self.assertRaises(StockReceivingError):
            _positive_integer("abc", "Quantity")


class ExpiryDateValidationTests(TestCase):

    def test_accepts_future_date(self):
        future_date = (
            timezone.localdate()
            + timedelta(days=365)
        )

        self.assertEqual(
            _expiry_date(future_date),
            future_date,
        )

    def test_accepts_iso_date_string(self):
        future_date = (
            timezone.localdate()
            + timedelta(days=365)
        )

        self.assertEqual(
            _expiry_date(future_date.isoformat()),
            future_date,
        )

    def test_rejects_expired_date(self):
        past_date = (
            timezone.localdate()
            - timedelta(days=1)
        )

        with self.assertRaises(StockReceivingError):
            _expiry_date(past_date)

    def test_rejects_today_expiry(self):
        with self.assertRaises(StockReceivingError):
            _expiry_date(timezone.localdate())

    def test_rejects_invalid_date_format(self):
        with self.assertRaises(StockReceivingError):
            _expiry_date("31/12/2027")

    def test_rejects_missing_expiry(self):
        with self.assertRaises(StockReceivingError):
            _expiry_date(None)


class ReceivingAccessValidationTests(TestCase):

    def make_user(
        self,
        *,
        authenticated=True,
        active=True,
        permitted=True,
    ):
        return SimpleNamespace(
            is_authenticated=authenticated,
            is_active=active,
            has_perm=lambda permission: (
                permitted
                and permission == "purchases.change_purchase"
            ),
        )

    def valid_payload(self):
        return [
            {
                "purchase_item_id": 1,
                "batch_number": "TEST-BATCH-001",
                "expiry_date": (
                    timezone.localdate()
                    + timedelta(days=365)
                ),
                "received_packs": 5,
            }
        ]

    def test_rejects_anonymous_user(self):
        user = self.make_user(
            authenticated=False
        )

        with self.assertRaises(StockReceivingError):
            receive_purchase_stock(
                purchase_id=1,
                received_by=user,
                items=self.valid_payload(),
                authorized_branches=None,
            )

    def test_rejects_inactive_user(self):
        user = self.make_user(active=False)

        with self.assertRaises(StockReceivingError):
            receive_purchase_stock(
                purchase_id=1,
                received_by=user,
                items=self.valid_payload(),
                authorized_branches=None,
            )

    def test_rejects_user_without_permission(self):
        user = self.make_user(permitted=False)

        with self.assertRaises(StockReceivingError):
            receive_purchase_stock(
                purchase_id=1,
                received_by=user,
                items=self.valid_payload(),
                authorized_branches=None,
            )

    def test_rejects_missing_authorized_branches(self):
        user = self.make_user()

        with self.assertRaisesMessage(
            StockReceivingError,
            "Authorized branches are required.",
        ):
            receive_purchase_stock(
                purchase_id=1,
                received_by=user,
                items=self.valid_payload(),
                authorized_branches=None,
            )

    def test_rejects_empty_receiving_items(self):
        user = self.make_user()

        with self.assertRaisesMessage(
            StockReceivingError,
            "Add at least one medicine to receive.",
        ):
            receive_purchase_stock(
                purchase_id=1,
                received_by=user,
                items=[],
                authorized_branches=object(),
            )

    def test_rejects_missing_user(self):
        with self.assertRaises(StockReceivingError):
            receive_purchase_stock(
                purchase_id=1,
                received_by=None,
                items=self.valid_payload(),
                authorized_branches=None,
            )
