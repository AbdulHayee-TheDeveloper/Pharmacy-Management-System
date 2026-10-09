from datetime import date, timedelta
from unittest.mock import patch

from django.test import SimpleTestCase

from .operational import (
    effective_low_stock_threshold,
    expiry_alert_category,
    get_operational_settings,
)


class OperationalSettingsTests(SimpleTestCase):
    def test_pharmacy_low_stock_floor_applies(self):
        self.assertEqual(effective_low_stock_threshold(10, 20), 20)

    def test_stricter_medicine_minimum_is_preserved(self):
        self.assertEqual(effective_low_stock_threshold(50, 20), 50)

    def test_zero_alert_window_includes_today(self):
        today = date(2026, 10, 9)
        self.assertEqual(expiry_alert_category(today, 0, today=today), "expiring_soon")

    def test_expired_yesterday_is_not_expiring_soon(self):
        today = date(2026, 10, 9)
        self.assertEqual(expiry_alert_category(today - timedelta(days=1), 30, today=today), "expired")

    def test_expiry_boundary_is_inclusive(self):
        today = date(2026, 10, 9)
        self.assertEqual(expiry_alert_category(today + timedelta(days=30), 30, today=today), "expiring_soon")
        self.assertEqual(expiry_alert_category(today + timedelta(days=31), 30, today=today), "valid")

    @patch("core_settings.operational.PharmacyProfile.objects.filter")
    def test_missing_profile_uses_defaults(self, mocked_filter):
        mocked_filter.return_value.values.return_value.first.return_value = None
        settings = get_operational_settings()
        self.assertEqual(settings["low_stock_threshold"], 20)
        self.assertEqual(settings["expiry_alert_days"], 30)
        self.assertEqual(settings["default_tax_percentage"], 0)
