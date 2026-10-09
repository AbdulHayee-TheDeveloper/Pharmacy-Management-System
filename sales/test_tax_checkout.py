
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from sales.models import Sale
from sales.services import CheckoutError, checkout_sale


class CheckoutTaxIntegrationTests(TestCase):
    """
    Exercise the real checkout_sale() calculation logic.

    Database writes are mocked to isolate:
    - effective tax rates
    - pack and loose-unit calculations
    - stock deductions
    - checkout validation

    These tests do not replace database integration tests.
    """

    def setUp(self):
        self.branch = SimpleNamespace(id=1)
        self.user = SimpleNamespace(id=1)

        self.medicine = SimpleNamespace(
            id=1,
            name="Test Medicine",
            is_active=True,
            pack_size=10,
            allow_loose_sale=True,
            tax_rate=Decimal("0.00"),
            use_pharmacy_default_tax=False,
            get_unit_display=lambda: "Tablet",
        )

        self.batch = SimpleNamespace(
            id=25,
            medicine=self.medicine,
            branch=self.branch,
            batch_number="BATCH-001",
            is_active=True,
            expiry_date=(
                timezone.localdate()
                + timedelta(days=365)
            ),
            quantity=100,
            selling_price=Decimal("100.00"),
            unit_selling_price=Decimal("10.00"),
            stock_display="10 packs",
            updated_at=None,
        )

        self.saved_sale = SimpleNamespace(
            id=100,
            invoice_number="SALE-TEST-001",
        )

        self.batch_queryset = MagicMock()
        self.batch_queryset.select_related.return_value = (
            self.batch_queryset
        )
        self.batch_queryset.filter.return_value = (
            self.batch_queryset
        )
        self.batch_queryset.__iter__.return_value = [
            self.batch
        ]

        self.patchers = [
            patch(
                "sales.services."
                "InventoryBatch.objects.select_for_update",
                return_value=self.batch_queryset,
            ),
            patch(
                "sales.services."
                "InventoryBatch.objects.bulk_update",
            ),
            patch(
                "sales.services.Sale.objects.create",
                return_value=self.saved_sale,
            ),
            patch("sales.services.SaleItem"),
            patch(
                "sales.services.get_default_tax_rate",
                return_value=Decimal("10.00"),
            ),
        ]

        self.mocks = [
            patcher.start()
            for patcher in self.patchers
        ]

        for patcher in self.patchers:
            self.addCleanup(patcher.stop)

        (
            self.lock_batches,
            self.bulk_update,
            self.create_sale,
            self.mock_sale_item,
            self.default_tax,
        ) = self.mocks

        self.mock_sale_item.objects.bulk_create = (
            MagicMock()
        )

    def checkout(self, items=None, **kwargs):
        if items is None:
            items = [
                {
                    "batch_id": self.batch.id,
                    "quantity": 1,
                    "sale_type": "pack",
                }
            ]

        return checkout_sale(
            user=self.user,
            branch=self.branch,
            items=items,
            payment_method=Sale.PaymentMethod.CASH,
            **kwargs,
        )

    def get_saved_values(self):
        return self.create_sale.call_args.kwargs

    def test_zero_percent_remains_tax_free(self):
        self.medicine.tax_rate = Decimal("0.00")
        self.medicine.use_pharmacy_default_tax = False

        self.checkout()

        saved = self.get_saved_values()

        self.assertEqual(
            saved["subtotal"],
            Decimal("100.00"),
        )
        self.assertEqual(
            saved["tax_amount"],
            Decimal("0.00"),
        )
        self.assertEqual(
            saved["total_amount"],
            Decimal("100.00"),
        )
        self.assertEqual(self.batch.quantity, 90)

    def test_medicine_specific_tax_overrides_default(self):
        self.medicine.tax_rate = Decimal("5.00")
        self.medicine.use_pharmacy_default_tax = False

        self.checkout()

        saved = self.get_saved_values()

        self.assertEqual(
            saved["tax_amount"],
            Decimal("5.00"),
        )
        self.assertEqual(
            saved["total_amount"],
            Decimal("105.00"),
        )

    def test_pharmacy_default_tax_is_applied(self):
        self.medicine.tax_rate = Decimal("5.00")
        self.medicine.use_pharmacy_default_tax = True

        self.checkout()

        saved = self.get_saved_values()

        self.assertEqual(
            saved["subtotal"],
            Decimal("100.00"),
        )
        self.assertEqual(
            saved["tax_amount"],
            Decimal("10.00"),
        )
        self.assertEqual(
            saved["total_amount"],
            Decimal("110.00"),
        )

    def test_loose_unit_uses_correct_tax(self):
        self.medicine.use_pharmacy_default_tax = True

        self.checkout(
            items=[
                {
                    "batch_id": self.batch.id,
                    "quantity": 3,
                    "sale_type": "unit",
                }
            ]
        )

        saved = self.get_saved_values()

        self.assertEqual(
            saved["subtotal"],
            Decimal("30.00"),
        )
        self.assertEqual(
            saved["tax_amount"],
            Decimal("3.00"),
        )
        self.assertEqual(
            saved["total_amount"],
            Decimal("33.00"),
        )
        self.assertEqual(self.batch.quantity, 97)

    def test_pack_and_loose_stock_deducted_together(self):
        self.medicine.use_pharmacy_default_tax = True
        self.batch.quantity = 25

        self.checkout(
            items=[
                {
                    "batch_id": self.batch.id,
                    "quantity": 1,
                    "sale_type": "pack",
                },
                {
                    "batch_id": self.batch.id,
                    "quantity": 3,
                    "sale_type": "unit",
                },
            ]
        )

        saved = self.get_saved_values()

        self.assertEqual(
            saved["subtotal"],
            Decimal("130.00"),
        )
        self.assertEqual(
            saved["tax_amount"],
            Decimal("13.00"),
        )
        self.assertEqual(
            saved["total_amount"],
            Decimal("143.00"),
        )

        # One pack (10 units) + 3 tablets.
        self.assertEqual(self.batch.quantity, 12)

        self.assertEqual(
            self.mock_sale_item.call_count,
            2,
        )
        self.bulk_update.assert_called_once()

    def test_insufficient_stock_rejects_sale(self):
        self.batch.quantity = 12

        with self.assertRaises(CheckoutError):
            self.checkout(
                items=[
                    {
                        "batch_id": self.batch.id,
                        "quantity": 1,
                        "sale_type": "pack",
                    },
                    {
                        "batch_id": self.batch.id,
                        "quantity": 3,
                        "sale_type": "unit",
                    },
                ]
            )

        self.create_sale.assert_not_called()
        self.bulk_update.assert_not_called()

    def test_frontend_tax_value_is_not_trusted(self):
        self.medicine.tax_rate = Decimal("5.00")
        self.medicine.use_pharmacy_default_tax = False

        self.checkout(
            items=[
                {
                    "batch_id": self.batch.id,
                    "quantity": 1,
                    "sale_type": "pack",
                    "tax_rate": "99.00",
                    "unit_price": "0.01",
                }
            ]
        )

        saved = self.get_saved_values()

        self.assertEqual(
            saved["subtotal"],
            Decimal("100.00"),
        )
        self.assertEqual(
            saved["tax_amount"],
            Decimal("5.00"),
        )
        self.assertEqual(
            saved["total_amount"],
            Decimal("105.00"),
        )
