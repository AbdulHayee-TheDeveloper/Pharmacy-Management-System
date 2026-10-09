
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import csv
import io

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase

from reports.services import (
    ReportValidationError,
    get_report_filters,
    money,
    scope_to_branch,
    user_is_admin,
)

from reports.views import (
    export_inventory_csv,
    safe_csv_cell,
)


class FakeUser:
    """
    Lightweight authenticated user for service tests.
    No database user is required.
    """

    is_authenticated = True
    is_active = True

    def __init__(
        self,
        *,
        is_superuser=False,
        role="cashier",
        branch_id=None,
        permissions=None,
    ):
        self.is_superuser = is_superuser
        self.role = role
        self.branch_id = branch_id
        self.permissions = permissions or set()

    def has_perm(self, permission):
        return (
            self.is_superuser
            or permission in self.permissions
        )


class ReportsSecurityTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def make_request(self, parameters=None, user=None):
        request = self.factory.get(
            "/reports/data/",
            data=parameters or {},
        )

        request.user = user or FakeUser(
            is_superuser=True
        )

        return request

    # --------------------------------------------------------
    # TEST 01 — ADMIN ACCESS
    # --------------------------------------------------------

    def test_superuser_is_admin(self):
        user = FakeUser(is_superuser=True)

        self.assertTrue(user_is_admin(user))

    # --------------------------------------------------------
    # TEST 02 — NORMAL STAFF ACCESS
    # --------------------------------------------------------

    def test_cashier_is_not_admin(self):
        user = FakeUser(
            role="cashier",
            branch_id=1,
        )

        self.assertFalse(user_is_admin(user))

    # --------------------------------------------------------
    # TEST 03 — INVALID DATE RANGE
    # --------------------------------------------------------

    def test_reverse_date_range_rejected(self):
        request = self.make_request({
            "date_from": "2026-10-10",
            "date_to": "2026-10-01",
        })

        with self.assertRaises(
            ReportValidationError
        ):
            get_report_filters(request)

    # --------------------------------------------------------
    # TEST 04 — OVERSIZED DATE RANGE
    # --------------------------------------------------------

    def test_date_range_above_limit_rejected(self):
        request = self.make_request({
            "date_from": "2024-01-01",
            "date_to": "2026-10-09",
        })

        with self.assertRaises(
            ReportValidationError
        ):
            get_report_filters(request)

    # --------------------------------------------------------
    # TEST 05 — CROSS-BRANCH REQUEST
    # --------------------------------------------------------

    def test_staff_cannot_select_other_branch(self):
        request = self.make_request(
            {"branch": "2"},
            FakeUser(
                branch_id=1,
                permissions={"sales.view_sale"},
            ),
        )

        with self.assertRaises(PermissionDenied):
            get_report_filters(request)

    # --------------------------------------------------------
    # TEST 06 — STAFF WITHOUT BRANCH
    # --------------------------------------------------------

    def test_staff_without_branch_denied(self):
        request = self.make_request(
            {},
            FakeUser(
                role="cashier",
                branch_id=None,
            ),
        )

        with self.assertRaises(PermissionDenied):
            get_report_filters(request)

    # --------------------------------------------------------
    # TEST 07 — SAME BRANCH ALLOWED
    # --------------------------------------------------------

    def test_staff_can_select_assigned_branch(self):
        request = self.make_request(
            {
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
                "branch": "4",
            },
            FakeUser(
                branch_id=4,
            ),
        )

        filters = get_report_filters(request)

        self.assertEqual(filters.branch_id, 4)
        self.assertEqual(
            filters.date_from,
            date(2026, 10, 1),
        )

    # --------------------------------------------------------
    # TEST 08 — QUERYSET BRANCH SCOPING
    # --------------------------------------------------------

    def test_queryset_branch_filter(self):
        queryset = MagicMock()

        filters = SimpleNamespace(
            branch_id=3
        )

        scope_to_branch(queryset, filters)

        queryset.filter.assert_called_once_with(
            branch_id=3
        )

    # --------------------------------------------------------
    # TEST 09 — MONEY ROUNDING
    # --------------------------------------------------------

    def test_money_rounding(self):
        self.assertEqual(
            money("12.345"),
            Decimal("12.35"),
        )

        self.assertEqual(
            money(None),
            Decimal("0.00"),
        )

    # --------------------------------------------------------
    # TEST 10 — CSV FORMULA PROTECTION
    # --------------------------------------------------------

    def test_csv_formula_injection_protection(self):
        self.assertEqual(
            safe_csv_cell("=2+2"),
            "'=2+2",
        )

        self.assertEqual(
            safe_csv_cell("+SUM(A1:A5)"),
            "'+SUM(A1:A5)",
        )

        self.assertEqual(
            safe_csv_cell("Paracetamol"),
            "Paracetamol",
        )


class InventoryExportTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    @patch("reports.views.get_inventory_report_queryset")
    def test_export_includes_more_than_100_batches(
        self,
        mock_get_queryset,
    ):
        """
        Inventory export should not stop after 100 rows.
        """

        today = date(2027, 1, 1)

        batches = []

        for index in range(125):
            batches.append(
                SimpleNamespace(
                    medicine=SimpleNamespace(
                        name=f"Medicine {index}",
                        pack_size=10,
                    ),
                    branch=SimpleNamespace(
                        name="Main Branch",
                    ),
                    batch_number=f"BATCH-{index:03d}",
                    quantity=20,
                    purchase_price=Decimal("100.00"),
                    selling_price=Decimal("150.00"),
                    expiry_date=today,
                    is_active=True,
                )
            )

        fake_queryset = MagicMock()

        fake_queryset.iterator.return_value = iter(
            batches
        )

        mock_get_queryset.return_value = fake_queryset

        request = self.factory.get(
            "/reports/export/inventory/",
            {
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        request.user = FakeUser(
            is_superuser=True,
            permissions={
                "inventory.view_inventorybatch"
            },
        )

        response = export_inventory_csv(request)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertTrue(response.streaming)

        # StreamingHttpResponse yields CSV chunks.
        content = b"".join(
            chunk if isinstance(chunk, bytes)
            else chunk.encode("utf-8")
            for chunk in response.streaming_content
        ).decode("utf-8-sig")

        rows = list(
            csv.reader(io.StringIO(content))
        )

        # One header + 125 inventory batch rows.
        self.assertEqual(len(rows), 126)

        self.assertEqual(
            rows[1][2],
            "BATCH-000",
        )

        self.assertEqual(
            rows[-1][2],
            "BATCH-124",
        )

        fake_queryset.iterator.assert_called_once_with(
            chunk_size=500
        )

# ============================================================
# PHASE 9.5 — FULL TRANSACTION CSV EXPORT TESTS
# ============================================================

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import RequestFactory, SimpleTestCase
from django.utils import timezone

from reports.views import (
    export_sales_csv,
    export_purchases_csv,
)


class FullTransactionExportTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

        self.user = FakeUser(
            is_superuser=True,
            permissions={
                "sales.view_sale",
                "purchases.view_purchase",
            },
        )

    def make_request(self, url):
        request = self.factory.get(
            url,
            {
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        request.user = self.user
        return request

    @staticmethod
    def csv_rows(response):
        import csv
        import io

        assert response.streaming

        content = b"".join(
            chunk if isinstance(chunk, bytes)
            else chunk.encode("utf-8")
            for chunk in response.streaming_content
        ).decode("utf-8-sig")

        return list(
            csv.reader(io.StringIO(content))
        )

    @patch("reports.views.get_sales_queryset")
    def test_sales_csv_exports_125_invoices(
        self,
        mock_get_queryset,
    ):
        completed_at = timezone.make_aware(
            datetime(2026, 10, 5, 12, 0)
        )

        rows = []

        for index in range(125):
            rows.append({
                "invoice_number": f"SALE-{index:04d}",
                "completed_at": completed_at,
                "branch__name": "Main Branch",
                "customer_name": "Walk-in Customer",
                "phone": "",
                "subtotal": Decimal("100.00"),
                "discount_amount": Decimal("0.00"),
                "tax_amount": Decimal("0.00"),
                "total_amount": Decimal("100.00"),
                "paid_amount": Decimal("100.00"),
                "change_amount": Decimal("0.00"),
                "payment_method": "cash",
                "payment_status": "paid",
                "status": "completed",
            })

        queryset = MagicMock()

        queryset.order_by.return_value.values.return_value.iterator.return_value = iter(
            rows
        )

        mock_get_queryset.return_value = queryset

        response = export_sales_csv(
            self.make_request(
                "/reports/export/sales/"
            )
        )

        self.assertEqual(response.status_code, 200)

        exported = self.csv_rows(response)

        self.assertEqual(len(exported), 126)
        self.assertEqual(exported[1][0], "SALE-0000")
        self.assertEqual(exported[-1][0], "SALE-0124")

    @patch("reports.views.get_purchase_queryset")
    def test_purchase_csv_exports_125_orders(
        self,
        mock_get_queryset,
    ):
        rows = []

        for index in range(125):
            rows.append({
                "purchase_number": f"PUR-{index:04d}",
                "purchase_date": date(2026, 10, 5),
                "branch__name": "Main Branch",
                "supplier__name": "Test Supplier",
                "supplier_invoice_number": "",
                "status": "ordered",
                "subtotal": Decimal("500.00"),
                "discount_amount": Decimal("0.00"),
                "tax_amount": Decimal("0.00"),
                "total_amount": Decimal("500.00"),
                "expected_delivery_date": None,
            })

        queryset = MagicMock()

        queryset.order_by.return_value.values.return_value.iterator.return_value = iter(
            rows
        )

        mock_get_queryset.return_value = queryset

        response = export_purchases_csv(
            self.make_request(
                "/reports/export/purchases/"
            )
        )

        self.assertEqual(response.status_code, 200)

        exported = self.csv_rows(response)

        self.assertEqual(len(exported), 126)
        self.assertEqual(exported[1][0], "PUR-0000")
        self.assertEqual(exported[-1][0], "PUR-0124")

    @patch("reports.views.get_sales_queryset")
    def test_sales_csv_excludes_returned_change(
        self,
        mock_get_queryset,
    ):
        completed_at = timezone.make_aware(
            datetime(2026, 10, 5, 12, 0)
        )

        sale = {
            "invoice_number": "SALE-CHANGE",
            "completed_at": completed_at,
            "branch__name": "Main Branch",
            "customer_name": "",
            "phone": "",
            "subtotal": Decimal("80.00"),
            "discount_amount": Decimal("0.00"),
            "tax_amount": Decimal("0.00"),
            "total_amount": Decimal("80.00"),
            "paid_amount": Decimal("100.00"),
            "change_amount": Decimal("20.00"),
            "payment_method": "cash",
            "payment_status": "paid",
            "status": "completed",
        }

        queryset = MagicMock()

        queryset.order_by.return_value.values.return_value.iterator.return_value = iter(
            [sale]
        )

        mock_get_queryset.return_value = queryset

        response = export_sales_csv(
            self.make_request(
                "/reports/export/sales/"
            )
        )

        exported = self.csv_rows(response)

        # Column 9: Net Collected
        # Column 10: Outstanding
        self.assertEqual(exported[1][9], "80.00")
        self.assertEqual(exported[1][10], "0.00")
