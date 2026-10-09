
# reports/test_pdf.py

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory, SimpleTestCase

from reports.pdf_reports import generate_report_pdf
from reports.views import export_report_pdf


class PDFUser:
    is_authenticated = True
    is_active = True

    def __init__(self, permissions=None):
        self.permissions = set(permissions or [])

    def has_perm(self, permission):
        return permission in self.permissions

    def get_full_name(self):
        return "Test Administrator"

    def get_username(self):
        return "testadmin"


class PDFGeneratorTests(SimpleTestCase):

    @patch("reports.pdf_reports.report_definition")
    def test_pdf_contains_valid_header(self, mock_definition):
        mock_definition.return_value = {
            "title": "Sales Report",
            "summary": [
                ("Sales Revenue", "Rs. 1,000.00"),
                ("Completed Sales", "2"),
            ],
            "headers": [
                "Invoice",
                "Customer",
                "Amount",
            ],
            "rows": [
                ["INV-001", "Customer A", "Rs. 500.00"],
                ["INV-002", "Customer B", "Rs. 500.00"],
            ],
            "note": "Test report.",
        }

        filters = SimpleNamespace(
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 9),
            branch_id=None,
        )

        pdf = generate_report_pdf(
            report_type="sales",
            filters=filters,
            generated_by="Test Administrator",
            branch_label="All Branches",
        )

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertIn(b"%%EOF", pdf[-1024:])
        self.assertGreater(len(pdf), 1000)

    @patch("reports.pdf_reports.report_definition")
    def test_pdf_supports_multiple_pages(self, mock_definition):
        mock_definition.return_value = {
            "title": "Inventory Report",
            "summary": [
                ("Batches", "150"),
            ],
            "headers": [
                "Medicine",
                "Batch",
                "Quantity",
            ],
            "rows": [
                [
                    f"Medicine {i}",
                    f"BATCH-{i:03d}",
                    "100",
                ]
                for i in range(150)
            ],
            "note": "Current inventory snapshot.",
        }

        filters = SimpleNamespace(
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 9),
            branch_id=None,
        )

        pdf = generate_report_pdf(
            report_type="inventory",
            filters=filters,
            generated_by="Test Administrator",
            branch_label="All Branches",
        )

        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertGreater(len(pdf), 3000)


class PDFExportViewTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def make_request(self, report_type, permissions):
        request = self.factory.get(
            f"/reports/pdf/{report_type}/",
            {
                "date_from": "2026-10-01",
                "date_to": "2026-10-09",
            },
        )

        request.user = PDFUser(permissions)

        return request

    @patch("reports.views.generate_report_pdf")
    @patch("reports.views.get_report_filters")
    def test_sales_pdf_download(
        self,
        mock_filters,
        mock_pdf,
    ):
        mock_filters.return_value = SimpleNamespace(
            date_from=date(2026, 10, 1),
            date_to=date(2026, 10, 9),
            branch_id=None,
        )

        mock_pdf.return_value = b"%PDF-1.4\nTEST"

        request = self.make_request(
            "sales",
            ["sales.view_sale"],
        )

        response = export_report_pdf(
            request,
            "sales",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )

        self.assertIn(
            ".pdf",
            response["Content-Disposition"],
        )

        self.assertEqual(
            response.content,
            b"%PDF-1.4\nTEST",
        )

    def test_unauthorized_sales_export_denied(self):
        request = self.make_request(
            "sales",
            [],
        )

        with self.assertRaises(PermissionDenied):
            export_report_pdf(
                request,
                "sales",
            )

    def test_profit_requires_both_permissions(self):
        request = self.make_request(
            "profit",
            ["sales.view_sale"],
        )

        with self.assertRaises(PermissionDenied):
            export_report_pdf(
                request,
                "profit",
            )

    def test_unknown_report_returns_404(self):
        request = self.make_request(
            "unknown",
            [],
        )

        with self.assertRaises(Http404):
            export_report_pdf(
                request,
                "unknown",
            )
