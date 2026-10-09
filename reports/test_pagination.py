
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.paginator import Paginator
from django.test import RequestFactory, SimpleTestCase

from reports.views import (
    paginate_report_queryset,
    paginated_response,
    sales_report_rows,
)


class ReportPaginationTests(SimpleTestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_paginator_returns_20_records(self):
        records = list(range(55))

        request = self.factory.get(
            "/reports/rows/sales/",
            {"page": "2"},
        )

        paginator, page = paginate_report_queryset(
            request,
            records,
        )

        self.assertEqual(paginator.count, 55)
        self.assertEqual(page.number, 2)
        self.assertEqual(len(page.object_list), 20)

    def test_last_page_has_15_records(self):
        records = list(range(55))

        request = self.factory.get(
            "/reports/rows/sales/",
            {"page": "3"},
        )

        paginator, page = paginate_report_queryset(
            request,
            records,
        )

        self.assertEqual(len(page.object_list), 15)
        self.assertFalse(page.has_next())

    def test_invalid_page_falls_back_safely(self):
        request = self.factory.get(
            "/reports/rows/sales/",
            {"page": "invalid"},
        )

        paginator, page = paginate_report_queryset(
            request,
            list(range(50)),
        )

        self.assertEqual(page.number, 1)

    def test_pagination_json_metadata(self):
        paginator = Paginator(
            list(range(55)),
            20,
        )

        page = paginator.page(2)

        response = paginated_response(
            paginator,
            page,
            [{"invoice_number": "INV-021"}],
        )

        import json

        data = json.loads(response.content)

        self.assertTrue(data["success"])

        self.assertEqual(
            data["data"]["pagination"]["total_records"],
            55,
        )

        self.assertEqual(
            data["data"]["pagination"]["total_pages"],
            3,
        )

        self.assertTrue(
            data["data"]["pagination"]["has_previous"]
        )

        self.assertTrue(
            data["data"]["pagination"]["has_next"]
        )
