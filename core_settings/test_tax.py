
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from core_settings.tax import get_effective_tax_rate


class EffectiveTaxRateTests(SimpleTestCase):

    def medicine(self, *, rate, use_default=False):
        return SimpleNamespace(
            tax_rate=Decimal(str(rate)),
            use_pharmacy_default_tax=use_default,
        )

    def test_zero_percent_is_tax_free(self):
        medicine = self.medicine(rate="0.00")

        result = get_effective_tax_rate(
            medicine,
            default_rate=Decimal("10.00"),
        )

        self.assertEqual(result, Decimal("0.00"))

    def test_medicine_specific_tax_is_preserved(self):
        medicine = self.medicine(rate="5.00")

        result = get_effective_tax_rate(
            medicine,
            default_rate=Decimal("10.00"),
        )

        self.assertEqual(result, Decimal("5.00"))

    def test_opted_in_medicine_uses_pharmacy_default(self):
        medicine = self.medicine(
            rate="5.00",
            use_default=True,
        )

        result = get_effective_tax_rate(
            medicine,
            default_rate=Decimal("10.00"),
        )

        self.assertEqual(result, Decimal("10.00"))

    def test_opted_in_medicine_can_use_zero_default(self):
        medicine = self.medicine(
            rate="12.00",
            use_default=True,
        )

        result = get_effective_tax_rate(
            medicine,
            default_rate=Decimal("0.00"),
        )

        self.assertEqual(result, Decimal("0.00"))

    def test_invalid_rate_is_rejected(self):
        medicine = self.medicine(rate="101.00")

        with self.assertRaises(ValueError):
            get_effective_tax_rate(
                medicine,
                default_rate=Decimal("10.00"),
            )

    @patch("core_settings.tax.get_default_tax_rate")
    def test_default_rate_is_loaded_when_not_supplied(
        self,
        mock_default,
    ):
        mock_default.return_value = Decimal("8.00")

        medicine = self.medicine(
            rate="0.00",
            use_default=True,
        )

        result = get_effective_tax_rate(medicine)

        self.assertEqual(result, Decimal("8.00"))
        mock_default.assert_called_once()
