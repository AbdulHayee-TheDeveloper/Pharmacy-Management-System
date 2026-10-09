
# reports/test_final.py

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase

from reports.services import (
    get_report_filters,
    ReportValidationError,
)

from reports.views import (
    sales_report_rows,
    purchase_report_rows,
    inventory_report_rows,
    export_report_pdf,
    export_sales_csv,
    export_inventory_csv,
)


class ReportTestUser:
    """
    Lightweight test user.

    This deliberately does not access
    the actual project database.
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
        self.permissions = set(
            permissions or []
        )

    def has_perm(self, permission):
        return (
            self.is_superuser
            or permission in self.permissions
        )

    def get_full_name(self):
        return "Test Administrator"

    def get_username(self):
        return "testadmin"


class ReportsFinalSecurityTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def make_request(
        self,
        url,
        params=None,
        user=None,
    ):
        request = self.factory.get(
            url,
            data=params or {},
        )

        request.user = user or ReportTestUser(
            is_superuser=True
        )

        return request

    # --------------------------------------------------------
    # TEST 01 — SALES SEARCH LENGTH VALIDATION
    # --------------------------------------------------------

    def test_sales_rejects_oversized_search(self):

        request = self.make_request(
            "/reports/rows/sales/",
            {
                "q": "A" * 101,
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        response = sales_report_rows(request)

        self.assertEqual(
            response.status_code,
            400,
        )

        import json

        data = json.loads(
            response.content
        )

        self.assertFalse(data["success"])

    # --------------------------------------------------------
    # TEST 02 — PURCHASE SEARCH LENGTH VALIDATION
    # --------------------------------------------------------

    def test_purchases_reject_oversized_search(self):

        request = self.make_request(
            "/reports/rows/purchases/",
            {
                "q": "B" * 101,
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        response = purchase_report_rows(
            request
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # --------------------------------------------------------
    # TEST 03 — INVENTORY SEARCH LENGTH VALIDATION
    # --------------------------------------------------------

    def test_inventory_rejects_oversized_search(self):

        request = self.make_request(
            "/reports/rows/inventory/",
            {
                "q": "C" * 101,
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        response = inventory_report_rows(
            request
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # --------------------------------------------------------
    # TEST 04 — INVALID DATE RANGE
    # --------------------------------------------------------

    def test_invalid_date_order_is_rejected(self):

        request = self.make_request(
            "/reports/rows/sales/",
            {
                "date_from": "2026-10-09",
                "date_to": "2026-10-01",
            },
        )

        response = sales_report_rows(
            request
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # --------------------------------------------------------
    # TEST 05 — SALES CSV CROSS-BRANCH SECURITY
    # --------------------------------------------------------

    def test_sales_csv_denies_other_branch(self):

        user = ReportTestUser(
            branch_id=1,
            permissions={
                "sales.view_sale",
            },
        )

        request = self.make_request(
            "/reports/export/sales/",
            {
                "branch": "2",
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
            user=user,
        )

        with self.assertRaises(
            PermissionDenied
        ):
            export_sales_csv(request)

    # --------------------------------------------------------
    # TEST 06 — INVENTORY CSV CROSS-BRANCH SECURITY
    # --------------------------------------------------------

    def test_inventory_csv_denies_other_branch(self):

        user = ReportTestUser(
            branch_id=1,
            permissions={
                "inventory.view_inventorybatch",
            },
        )

        request = self.make_request(
            "/reports/export/inventory/",
            {
                "branch": "2",
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
            user=user,
        )

        with self.assertRaises(
            PermissionDenied
        ):
            export_inventory_csv(request)

    # --------------------------------------------------------
    # TEST 07 — PDF CROSS-BRANCH SECURITY
    # --------------------------------------------------------

    def test_pdf_denies_other_branch(self):

        user = ReportTestUser(
            branch_id=1,
            permissions={
                "sales.view_sale",
            },
        )

        request = self.make_request(
            "/reports/pdf/sales/",
            {
                "branch": "2",
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
            user=user,
        )

        with self.assertRaises(
            PermissionDenied
        ):
            export_report_pdf(
                request,
                "sales",
            )

    # --------------------------------------------------------
    # TEST 08 — PDF INVALID DATE RETURNS 400
    # --------------------------------------------------------

    def test_pdf_rejects_invalid_date(self):

        request = self.make_request(
            "/reports/pdf/sales/",
            {
                "date_from": "2026-10-09",
                "date_to": "2026-10-01",
            },
        )

        response = export_report_pdf(
            request,
            "sales",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    # --------------------------------------------------------
    # TEST 09 — PDF USES AUTHORIZED BRANCH FILTER
    # --------------------------------------------------------

    @patch("reports.views.generate_report_pdf")
    @patch("reports.views.Branch.objects.filter")
    def test_pdf_uses_selected_branch(
        self,
        mock_branch_filter,
        mock_pdf,
    ):
        mock_pdf.return_value = (
            b"%PDF-1.4\nTEST\n%%EOF"
        )

        mock_branch_filter.return_value.values_list.return_value.first.return_value = (
            "Main Branch"
        )

        request = self.make_request(
            "/reports/pdf/sales/",
            {
                "branch": "1",
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        response = export_report_pdf(
            request,
            "sales",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        mock_pdf.assert_called_once()

        arguments = mock_pdf.call_args.kwargs

        self.assertEqual(
            arguments["report_type"],
            "sales",
        )

        self.assertEqual(
            arguments["filters"].branch_id,
            1,
        )

        self.assertEqual(
            arguments["branch_label"],
            "Main Branch",
        )
