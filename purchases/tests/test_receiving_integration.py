
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from branches.models import Branch
from inventory.models import InventoryBatch
from medicines.models import Category, Medicine
from purchases.models import (
    Purchase,
    PurchaseItem,
    PurchaseReceipt,
    PurchaseReceiptItem,
)
from purchases.services import (
    StockReceivingError,
    receive_purchase_stock,
)
from suppliers.models import Supplier


class PurchaseReceivingIntegrationTests(TestCase):
    """
    Real database integration tests.

    Django creates an isolated test database.
    Existing production/development records are not modified.
    """

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_superuser(
            username="receiving_test_admin",
            email="receiving-test@example.com",
            password="TestingPassword123!",
        )

        self.branch = Branch.objects.create(
            name="Test Main Branch",
            code="TEST-MAIN",
        )

        self.other_branch = Branch.objects.create(
            name="Test Other Branch",
            code="TEST-OTHER",
        )

        self.supplier = Supplier.objects.create(
            name="Test Supplier",
            company_name="Test Pharma",
            phone="03000000000",
        )

        self.category = Category.objects.create(
            name="Test Tablets",
        )

        self.medicine = Medicine.objects.create(
            name="Test Paracetamol",
            category=self.category,
            pack_size=10,
            unit=Medicine.Unit.TABLET,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
        )

        self.purchase = Purchase.objects.create(
            supplier=self.supplier,
            branch=self.branch,
            created_by=self.user,
            status=Purchase.Status.ORDERED,
        )

        self.item = PurchaseItem.objects.create(
            purchase=self.purchase,
            medicine=self.medicine,
            ordered_packs=10,
            received_packs=0,
            pack_size=10,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
        )

        self.future_expiry = (
            timezone.localdate() + timedelta(days=365)
        )

    def row(
        self,
        *,
        packs=5,
        batch="TEST-BATCH-001",
        expiry=None,
        purchase_item=None,
    ):
        return {
            "purchase_item_id": (
                purchase_item.pk
                if purchase_item is not None
                else self.item.pk
            ),
            "batch_number": batch,
            "expiry_date": (
                expiry
                if expiry is not None
                else self.future_expiry
            ),
            "received_packs": packs,
        }

    def receive(
        self,
        rows=None,
        *,
        purchase=None,
        user=None,
        branches=None,
    ):
        return receive_purchase_stock(
            purchase_id=(
                purchase.pk
                if purchase is not None
                else self.purchase.pk
            ),
            received_by=user or self.user,
            items=(
                rows
                if rows is not None
                else [self.row()]
            ),
            authorized_branches=(
                branches
                if branches is not None
                else Branch.objects.filter(
                    pk=self.branch.pk
                )
            ),
            supplier_delivery_note="TEST-DELIVERY",
        )

    def refresh(self):
        self.purchase.refresh_from_db()
        self.item.refresh_from_db()

    # --------------------------------------------------------
    # 1. PARTIAL RECEIVING
    # --------------------------------------------------------

    def test_partial_receiving(self):
        receipt = self.receive(
            [self.row(packs=6)]
        )

        self.refresh()

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.PARTIALLY_RECEIVED,
        )
        self.assertEqual(self.item.received_packs, 6)
        self.assertEqual(self.item.remaining_packs, 4)

        self.assertEqual(receipt.total_received_packs, 6)

        self.assertEqual(
            PurchaseReceipt.objects.count(),
            1,
        )

    # --------------------------------------------------------
    # 2. PACK-TO-UNIT STOCK CONVERSION
    # --------------------------------------------------------

    def test_pack_conversion(self):
        self.receive([self.row(packs=5)])

        batch = InventoryBatch.objects.get(
            medicine=self.medicine,
            branch=self.branch,
            batch_number="TEST-BATCH-001",
        )

        # 5 packs x 10 tablets = 50 tablets
        self.assertEqual(batch.quantity, 50)
        self.assertEqual(batch.full_packs_available, 5)
        self.assertEqual(batch.loose_units_available, 0)

    # --------------------------------------------------------
    # 3. FULL RECEIVING
    # --------------------------------------------------------

    def test_full_receiving(self):
        self.receive([self.row(packs=10)])

        self.refresh()

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.RECEIVED,
        )
        self.assertEqual(self.item.received_packs, 10)
        self.assertEqual(self.item.remaining_packs, 0)

        batch = InventoryBatch.objects.get(
            medicine=self.medicine,
            branch=self.branch,
            batch_number="TEST-BATCH-001",
        )

        self.assertEqual(batch.quantity, 100)

    # --------------------------------------------------------
    # 4. MULTIPLE PARTIAL DELIVERIES
    # --------------------------------------------------------

    def test_multiple_partial_deliveries(self):
        self.receive([
            self.row(packs=4, batch="BATCH-A")
        ])

        self.refresh()

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.PARTIALLY_RECEIVED,
        )

        self.receive([
            self.row(packs=6, batch="BATCH-B")
        ])

        self.refresh()

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.RECEIVED,
        )
        self.assertEqual(self.item.received_packs, 10)

        self.assertEqual(
            PurchaseReceipt.objects.count(),
            2,
        )
        self.assertEqual(
            PurchaseReceiptItem.objects.count(),
            2,
        )

        total_units = sum(
            InventoryBatch.objects.values_list(
                "quantity",
                flat=True,
            )
        )

        self.assertEqual(total_units, 100)

    # --------------------------------------------------------
    # 5. OVER-RECEIVING REJECTED
    # --------------------------------------------------------

    def test_over_receiving_rejected(self):
        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(packs=11)
            ])

        self.refresh()

        self.assertEqual(self.item.received_packs, 0)
        self.assertEqual(
            InventoryBatch.objects.count(),
            0,
        )
        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 6. DUPLICATE BATCH IN SAME DELIVERY
    # --------------------------------------------------------

    def test_duplicate_batch_rejected(self):
        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(packs=2, batch="SAME-BATCH"),
                self.row(packs=3, batch="SAME-BATCH"),
            ])

        self.assertEqual(
            InventoryBatch.objects.count(),
            0,
        )
        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 7. EXPIRED BATCH REJECTED
    # --------------------------------------------------------

    def test_expired_batch_rejected(self):
        expired_date = (
            timezone.localdate()
            - timedelta(days=1)
        )

        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(
                    packs=5,
                    expiry=expired_date,
                )
            ])

        self.assertEqual(
            InventoryBatch.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 8. UNAUTHORIZED BRANCH REJECTED
    # --------------------------------------------------------

    def test_unauthorized_branch_rejected(self):
        other_branches = Branch.objects.filter(
            pk=self.other_branch.pk
        )

        with self.assertRaises(StockReceivingError):
            self.receive(
                branches=other_branches
            )

        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 9. COMPLETED PURCHASE CANNOT BE RECEIVED AGAIN
    # --------------------------------------------------------

    def test_completed_purchase_cannot_receive_again(self):
        self.receive([self.row(packs=10)])

        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(packs=1, batch="SECOND-BATCH")
            ])

        self.refresh()

        self.assertEqual(self.item.received_packs, 10)
        self.assertEqual(
            PurchaseReceipt.objects.count(),
            1,
        )
        self.assertEqual(
            InventoryBatch.objects.count(),
            1,
        )

    # --------------------------------------------------------
    # 10. EXISTING BATCH QUANTITY INCREASES
    # --------------------------------------------------------

    def test_existing_batch_stock_increases(self):
        self.receive([
            self.row(packs=3, batch="BATCH-EXISTING")
        ])

        self.receive([
            self.row(packs=2, batch="BATCH-EXISTING")
        ])

        batch = InventoryBatch.objects.get(
            medicine=self.medicine,
            branch=self.branch,
            batch_number="BATCH-EXISTING",
        )

        self.refresh()

        self.assertEqual(batch.quantity, 50)
        self.assertEqual(self.item.received_packs, 5)
        self.assertEqual(
            PurchaseReceipt.objects.count(),
            2,
        )

    # --------------------------------------------------------
    # 11. MISMATCHED EXISTING BATCH EXPIRY REJECTED
    # --------------------------------------------------------

    def test_existing_batch_expiry_mismatch(self):
        InventoryBatch.objects.create(
            medicine=self.medicine,
            branch=self.branch,
            batch_number="EXISTING-BATCH",
            expiry_date=(
                self.future_expiry
                + timedelta(days=30)
            ),
            quantity=20,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
        )

        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(
                    packs=5,
                    batch="EXISTING-BATCH",
                )
            ])

        batch = InventoryBatch.objects.get(
            batch_number="EXISTING-BATCH"
        )

        self.refresh()

        self.assertEqual(batch.quantity, 20)
        self.assertEqual(self.item.received_packs, 0)
        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 12. TRANSACTION ROLLBACK AFTER PARTIAL PROCESSING
    # --------------------------------------------------------

    def test_transaction_rolls_back_everything(self):
        """
        First batch would be created and incremented.

        Second batch already exists but has an
        incompatible expiry date.

        The entire transaction must roll back.
        """

        InventoryBatch.objects.create(
            medicine=self.medicine,
            branch=self.branch,
            batch_number="ZZZ-CONFLICT",
            expiry_date=(
                self.future_expiry
                + timedelta(days=20)
            ),
            quantity=25,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
        )

        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(
                    packs=2,
                    batch="AAA-NEW",
                ),
                self.row(
                    packs=3,
                    batch="ZZZ-CONFLICT",
                ),
            ])

        self.refresh()

        # The earlier successful batch update
        # must also be rolled back.
        self.assertFalse(
            InventoryBatch.objects.filter(
                batch_number="AAA-NEW"
            ).exists()
        )

        conflict_batch = InventoryBatch.objects.get(
            batch_number="ZZZ-CONFLICT"
        )

        self.assertEqual(conflict_batch.quantity, 25)
        self.assertEqual(self.item.received_packs, 0)

        self.assertEqual(
            self.purchase.status,
            Purchase.Status.ORDERED,
        )

        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

        self.assertEqual(
            PurchaseReceiptItem.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 13. USER WITHOUT PERMISSION
    # --------------------------------------------------------

    def test_user_without_permission_rejected(self):
        User = get_user_model()

        ordinary_user = User.objects.create_user(
            username="no_receiving_permission",
            password="TestingPassword123!",
            branch=self.branch,
        )

        with self.assertRaises(StockReceivingError):
            self.receive(user=ordinary_user)

        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 14. UNRELATED PURCHASE ITEM
    # --------------------------------------------------------

    def test_unrelated_purchase_item_rejected(self):
        another_purchase = Purchase.objects.create(
            supplier=self.supplier,
            branch=self.branch,
            created_by=self.user,
            status=Purchase.Status.ORDERED,
        )

        another_item = PurchaseItem.objects.create(
            purchase=another_purchase,
            medicine=self.medicine,
            ordered_packs=5,
            pack_size=10,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
        )

        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(
                    purchase_item=another_item,
                )
            ])

        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )

    # --------------------------------------------------------
    # 15. INACTIVE INVENTORY BATCH REJECTED
    # --------------------------------------------------------

    def test_inactive_batch_rejected(self):
        InventoryBatch.objects.create(
            medicine=self.medicine,
            branch=self.branch,
            batch_number="INACTIVE-BATCH",
            expiry_date=self.future_expiry,
            quantity=10,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
            is_active=False,
        )

        with self.assertRaises(StockReceivingError):
            self.receive([
                self.row(
                    packs=5,
                    batch="INACTIVE-BATCH",
                )
            ])

        batch = InventoryBatch.objects.get(
            batch_number="INACTIVE-BATCH"
        )

        self.assertEqual(batch.quantity, 10)
        self.assertEqual(
            PurchaseReceipt.objects.count(),
            0,
        )
