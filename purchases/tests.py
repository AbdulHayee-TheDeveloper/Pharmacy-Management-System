
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from branches.models import Branch
from core_settings.models import PharmacyProfile
from medicines.models import Category, Medicine
from purchases.email_services import send_purchase_order_email
from purchases.models import (
    Purchase,
    PurchaseItem,
    PurchaseOrderEmail,
)
from suppliers.models import Supplier


TEST_MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
        "OPTIONS": {},
    },
}


@override_settings(MAILERS=TEST_MAILERS)
class PurchaseEmailTests(TestCase):
    """
    Supplier purchase email and retry tests.

    No real SMTP requests are performed.
    The test database is isolated.
    """

    def setUp(self):
        User = get_user_model()

        self.admin = User.objects.create_superuser(
            username="email_test_admin",
            email="admin@example.com",
            password="TestingPassword123!",
        )

        self.branch = Branch.objects.create(
            name="Email Test Main",
            code="EMAIL-MAIN",
        )

        self.other_branch = Branch.objects.create(
            name="Email Test Other",
            code="EMAIL-OTHER",
        )

        # These fixtures contain multiple branches,
        # so explicitly enable Multi-Branch Mode.
        profile = PharmacyProfile.get_profile()
        profile.enable_multi_branch = True
        profile.save(update_fields=["enable_multi_branch"])

        self.supplier = Supplier.objects.create(
            name="Email Test Supplier",
            company_name="Test Pharma Company",
            phone="03000000000",
            email="supplier@example.com",
        )

        self.category = Category.objects.create(
            name="Email Test Tablets",
        )

        self.medicine = Medicine.objects.create(
            name="Email Test Paracetamol",
            category=self.category,
            pack_size=10,
            unit=Medicine.Unit.TABLET,
            purchase_price=Decimal("100.00"),
            selling_price=Decimal("130.00"),
        )

        self.purchase = Purchase.objects.create(
            supplier=self.supplier,
            branch=self.branch,
            created_by=self.admin,
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

        self.notification = PurchaseOrderEmail.objects.create(
            purchase=self.purchase,
            recipient_email="supplier@example.com",
            status=PurchaseOrderEmail.Status.PENDING,
        )

        self.retry_url = reverse(
            "purchases:retry_email",
            kwargs={"pk": self.purchase.pk},
        )

        self.client.force_login(self.admin)

    def refresh(self):
        self.purchase.refresh_from_db()
        self.notification.refresh_from_db()

    # --------------------------------------------------
    # EMAIL DELIVERY SERVICE
    # --------------------------------------------------

    def test_pending_email_sends_successfully(self):
        result = send_purchase_order_email(
            self.notification.pk
        )

        self.refresh()

        self.assertTrue(result)
        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.SENT,
        )
        self.assertEqual(self.notification.attempts, 1)
        self.assertIsNotNone(self.notification.sent_at)

        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(
            email.to,
            ["supplier@example.com"],
        )
        self.assertIn(
            self.purchase.purchase_number,
            email.subject,
        )
        self.assertIn(
            self.medicine.name,
            email.body,
        )
        self.assertIn(
            "10 packs",
            email.body,
        )

    def test_sent_email_is_not_sent_again(self):
        self.notification.status = (
            PurchaseOrderEmail.Status.SENT
        )
        self.notification.save(
            update_fields=["status"]
        )

        result = send_purchase_order_email(
            self.notification.pk
        )

        self.refresh()

        self.assertFalse(result)
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_sending_email_is_not_sent_again(self):
        self.notification.status = (
            PurchaseOrderEmail.Status.SENDING
        )
        self.notification.save(
            update_fields=["status"]
        )

        result = send_purchase_order_email(
            self.notification.pk
        )

        self.refresh()

        self.assertFalse(result)
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_email_failure_is_recorded(self):
        with patch(
            "purchases.email_services.EmailMessage.send",
            side_effect=ConnectionError("SMTP unavailable"),
        ):
            result = send_purchase_order_email(
                self.notification.pk
            )

        self.refresh()

        self.assertFalse(result)

        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.FAILED,
        )
        self.assertEqual(self.notification.attempts, 1)
        self.assertIn(
            "SMTP unavailable",
            self.notification.last_error,
        )

        # Email failure must not cancel purchase.
        self.assertEqual(
            self.purchase.status,
            Purchase.Status.ORDERED,
        )

    def test_missing_recipient_is_recorded_as_failure(self):
        self.notification.recipient_email = ""
        self.notification.save(
            update_fields=["recipient_email"]
        )

        result = send_purchase_order_email(
            self.notification.pk
        )

        self.refresh()

        self.assertFalse(result)
        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.FAILED,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_failed_email_can_be_sent_later(self):
        self.notification.status = (
            PurchaseOrderEmail.Status.FAILED
        )
        self.notification.last_error = "Previous SMTP error"
        self.notification.attempts = 1
        self.notification.save(
            update_fields=[
                "status",
                "last_error",
                "attempts",
            ]
        )

        result = send_purchase_order_email(
            self.notification.pk
        )

        self.refresh()

        self.assertTrue(result)
        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.SENT,
        )
        self.assertEqual(self.notification.attempts, 2)
        self.assertEqual(self.notification.last_error, "")
        self.assertEqual(len(mail.outbox), 1)

    # --------------------------------------------------
    # RETRY ENDPOINT
    # --------------------------------------------------

    def test_retry_pending_email(self):
        response = self.client.post(self.retry_url)

        self.refresh()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.SENT,
        )
        self.assertEqual(self.notification.attempts, 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_retry_failed_email(self):
        self.notification.status = (
            PurchaseOrderEmail.Status.FAILED
        )
        self.notification.save(
            update_fields=["status"]
        )

        response = self.client.post(self.retry_url)

        self.refresh()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.SENT,
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_retry_sent_email_is_blocked(self):
        self.notification.status = (
            PurchaseOrderEmail.Status.SENT
        )
        self.notification.save(
            update_fields=["status"]
        )

        response = self.client.post(self.retry_url)

        self.refresh()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.notification.status,
            PurchaseOrderEmail.Status.SENT,
        )
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_retry_sending_email_is_blocked(self):
        self.notification.status = (
            PurchaseOrderEmail.Status.SENDING
        )
        self.notification.save(
            update_fields=["status"]
        )

        response = self.client.post(self.retry_url)

        self.refresh()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_retry_draft_purchase_is_blocked(self):
        self.purchase.status = Purchase.Status.DRAFT
        self.purchase.save(update_fields=["status"])

        response = self.client.post(self.retry_url)

        self.refresh()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_retry_cancelled_purchase_is_blocked(self):
        self.purchase.status = Purchase.Status.CANCELLED
        self.purchase.save(update_fields=["status"])

        response = self.client.post(self.retry_url)

        self.refresh()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_retry_requires_post(self):
        response = self.client.get(self.retry_url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(len(mail.outbox), 0)

    def test_anonymous_user_cannot_retry(self):
        self.client.logout()

        response = self.client.post(self.retry_url)

        self.assertEqual(response.status_code, 302)

        self.notification.refresh_from_db()
        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_user_without_permission_cannot_retry(self):
        User = get_user_model()

        employee = User.objects.create_user(
            username="email_test_employee",
            password="TestingPassword123!",
            branch=self.branch,
        )

        self.client.force_login(employee)

        response = self.client.post(self.retry_url)

        self.assertIn(
            response.status_code,
            [302, 403],
        )

        self.notification.refresh_from_db()

        self.assertEqual(self.notification.attempts, 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_notification_does_not_create_email(self):
        self.notification.delete()

        response = self.client.post(self.retry_url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            PurchaseOrderEmail.objects.count(),
            0,
        )
        self.assertEqual(len(mail.outbox), 0)
