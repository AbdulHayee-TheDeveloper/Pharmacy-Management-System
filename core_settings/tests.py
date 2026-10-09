
from decimal import Decimal
from types import SimpleNamespace
from django.contrib.auth import get_user_model
from django.core.exceptions import (
    PermissionDenied,
    ValidationError,
)
from django.test import (
    RequestFactory,
    TestCase,
)

from .forms import PharmacyProfileForm
from .models import PharmacyProfile
from .views import (
    can_manage_pharmacy_settings,
    pharmacy_settings,
)


class PharmacyProfileModelTests(TestCase):

    def test_default_profile_created(self):
        profile = PharmacyProfile.get_profile()

        self.assertEqual(profile.pk, 1)
        self.assertEqual(
            profile.name,
            "PharmaCare",
        )

    def test_profile_is_singleton(self):
        first = PharmacyProfile.get_profile()
        second = PharmacyProfile.get_profile()

        self.assertEqual(first.pk, second.pk)

        self.assertEqual(
            PharmacyProfile.objects.count(),
            1,
        )

    def test_profile_persists_updates(self):
        profile = PharmacyProfile.get_profile()

        profile.name = "My Pharmacy"
        profile.default_tax_percentage = Decimal("5.00")
        profile.save()

        profile.refresh_from_db()

        self.assertEqual(
            profile.name,
            "My Pharmacy",
        )

        self.assertEqual(
            profile.default_tax_percentage,
            Decimal("5.00"),
        )

    def test_tax_above_100_rejected(self):
        profile = PharmacyProfile.get_profile()

        profile.default_tax_percentage = Decimal("101.00")

        with self.assertRaises(ValidationError):
            profile.save()

    def test_negative_tax_rejected(self):
        profile = PharmacyProfile.get_profile()

        profile.default_tax_percentage = Decimal("-1.00")

        with self.assertRaises(ValidationError):
            profile.save()

    def test_expiry_days_above_365_rejected(self):
        profile = PharmacyProfile.get_profile()

        profile.expiry_alert_days = 366

        with self.assertRaises(ValidationError):
            profile.save()


class PharmacySettingsPermissionTests(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def make_user(
        self,
        *,
        superuser=False,
        permission=False,
    ):
        return SimpleNamespace(
            is_authenticated=True,
            is_superuser=superuser,
            has_perm=(
                lambda codename: (
                    permission
                    and codename
                    == "core_settings.change_pharmacyprofile"
                )
            ),
        )

    def test_superuser_can_manage_settings(self):
        user = self.make_user(superuser=True)

        self.assertTrue(
            can_manage_pharmacy_settings(user)
        )

    def test_staff_without_permission_denied(self):
        user = self.make_user()

        self.assertFalse(
            can_manage_pharmacy_settings(user)
        )

        request = self.factory.get(
            "/settings/pharmacy/"
        )

        request.user = user

        with self.assertRaises(PermissionDenied):
            pharmacy_settings(request)

    def test_explicit_permission_allows_access(self):
        user = self.make_user(permission=True)

        self.assertTrue(
            can_manage_pharmacy_settings(user)
        )

    def test_superuser_can_open_settings(self):

        User = get_user_model()

        admin = User.objects.create_superuser(
            username="pharmacy_test_admin",
            email="admin@example.com",
            password="TestAdmin@12345",
        )

        request = self.factory.get(
            "/settings/pharmacy/"
        )

        request.user = admin

        response = pharmacy_settings(request)

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Pharmacy Settings",
        )


class PharmacyProfileFormTests(TestCase):

    def test_valid_settings_form(self):
        profile = PharmacyProfile.get_profile()

        form = PharmacyProfileForm(
            data={
                "name": "Test Pharmacy",
                "tagline": "Quality Medicines",
                "phone": "03001234567",
                "email": "test@example.com",
                "address": "Faisalabad",
                "registration_number": "REG-001",
                "currency_code": "PKR",
                "default_tax_percentage": "5.50",
                "low_stock_threshold": "20",
                "expiry_alert_days": "30",
                "receipt_footer": "Thank you!",
            },
            instance=profile,
        )

        self.assertTrue(
            form.is_valid(),
            form.errors,
        )

    def test_invalid_email_rejected(self):
        profile = PharmacyProfile.get_profile()

        form = PharmacyProfileForm(
            data={
                "name": "Test Pharmacy",
                "email": "not-a-valid-email",
                "currency_code": "PKR",
                "default_tax_percentage": "0",
                "low_stock_threshold": "20",
                "expiry_alert_days": "30",
            },
            instance=profile,
        )

        self.assertFalse(form.is_valid())

        self.assertIn(
            "email",
            form.errors,
        )
