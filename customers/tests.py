
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from branches.models import Branch
from customers.models import (
    Customer,
    CustomerSaleLinkAudit,
)
from sales.models import Sale, SalePayment


# ============================================================
# PHASE 8.5 — CUSTOMER MANAGEMENT AUTOMATED TESTS
# ============================================================


class CustomerManagementTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        User = get_user_model()

        # ----------------------------------------------------
        # BRANCHES
        # ----------------------------------------------------

        cls.branch_a = Branch.objects.create(
            name="Test Branch A",
            code="TEST-BR-A",
        )

        cls.branch_b = Branch.objects.create(
            name="Test Branch B",
            code="TEST-BR-B",
        )

        # ----------------------------------------------------
        # SUPERUSER
        # ----------------------------------------------------

        cls.admin = User.objects.create_superuser(
            username="test_customer_admin",
            email="testadmin@example.com",
            password="TestPassword123!",
        )

        # Assign Branch A so sales queries are branch-scoped.
        cls.admin.branch = cls.branch_a
        cls.admin.save(update_fields=["branch"])

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------

        cls.customer = Customer.objects.create(
            name="Muhammad Ali",
            phone="03001234567",
            email="ali@example.com",
            city="Faisalabad",
            customer_type=Customer.CustomerType.REGULAR,
            is_active=True,
        )

        cls.wholesale_customer = Customer.objects.create(
            name="Ahmed Pharmacy",
            phone="03111234567",
            customer_type=Customer.CustomerType.WHOLESALE,
            is_active=True,
        )

        cls.inactive_customer = Customer.objects.create(
            name="Inactive Customer",
            is_active=False,
        )

        # ----------------------------------------------------
        # COMPLETED SALE — BRANCH A
        # ----------------------------------------------------

        cls.sale_a = Sale.objects.create(
            branch=cls.branch_a,
            cashier=cls.admin,
            customer=cls.customer,
            customer_name=cls.customer.name,
            customer_phone=cls.customer.phone,
            subtotal=Decimal("500.00"),
            total_amount=Decimal("500.00"),
            paid_amount=Decimal("300.00"),
            change_amount=Decimal("0.00"),
            payment_method=Sale.PaymentMethod.CASH,
            payment_status=Sale.PaymentStatus.PARTIAL,
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        # ----------------------------------------------------
        # COMPLETED SALE — BRANCH B
        # ----------------------------------------------------

        cls.sale_b = Sale.objects.create(
            branch=cls.branch_b,
            cashier=cls.admin,
            customer=cls.customer,
            customer_name=cls.customer.name,
            customer_phone=cls.customer.phone,
            subtotal=Decimal("1000.00"),
            total_amount=Decimal("1000.00"),
            paid_amount=Decimal("0.00"),
            change_amount=Decimal("0.00"),
            payment_method=Sale.PaymentMethod.CASH,
            payment_status=Sale.PaymentStatus.UNPAID,
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        # ----------------------------------------------------
        # ADDITIONAL PAYMENT — BRANCH A
        # ----------------------------------------------------

        # Sale A total: 500
        # Already paid: 300
        # Outstanding: 200
        #
        # The additional payment is part of the 300 already
        # recorded in Sale.paid_amount. Do not add it twice.

        cls.payment_a = SalePayment.objects.create(
            sale=cls.sale_a,
            amount=Decimal("100.00"),
            payment_method="cash",
            received_by=cls.admin,
        )

        # ----------------------------------------------------
        # ADDITIONAL PAYMENT — BRANCH B
        # ----------------------------------------------------

        cls.payment_b = SalePayment.objects.create(
            sale=cls.sale_b,
            amount=Decimal("50.00"),
            payment_method="cash",
            received_by=cls.admin,
        )

        # ----------------------------------------------------
        # UNLINKED HISTORICAL SALE — BRANCH A
        # ----------------------------------------------------

        cls.unlinked_sale = Sale.objects.create(
            branch=cls.branch_a,
            cashier=cls.admin,
            customer=None,
            customer_name="Muhammad Ali",
            customer_phone="03001234567",
            subtotal=Decimal("250.00"),
            total_amount=Decimal("250.00"),
            paid_amount=Decimal("250.00"),
            change_amount=Decimal("0.00"),
            payment_method=Sale.PaymentMethod.CASH,
            payment_status=Sale.PaymentStatus.PAID,
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.admin)

    # ========================================================
    # TEST 01 — CUSTOMER CODE GENERATION
    # ========================================================

    def test_customer_code_generated(self):

        self.assertIsNotNone(
            self.customer.customer_code
        )

        self.assertTrue(
            self.customer.customer_code.startswith(
                "CUS-"
            )
        )

    # ========================================================
    # TEST 02 — CUSTOMER LIST PAGE
    # ========================================================

    def test_customer_list_loads(self):

        response = self.client.get(
            reverse("customers:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Muhammad Ali",
        )

        self.assertEqual(
            response.context["total_customers"],
            3,
        )

    # ========================================================
    # TEST 03 — CUSTOMER AJAX SEARCH
    # ========================================================

    def test_customer_ajax_search(self):

        response = self.client.get(
            reverse("customers:list"),
            {"q": "Muhammad"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        data = response.json()

        self.assertIn("html", data)

        self.assertIn(
            "Muhammad Ali",
            data["html"],
        )

        self.assertNotIn(
            "Ahmed Pharmacy",
            data["html"],
        )

    # ========================================================
    # TEST 04 — CUSTOMER STATUS FILTER
    # ========================================================

    def test_active_customer_filter(self):

        response = self.client.get(
            reverse("customers:list"),
            {"status": "active"},
        )

        customers = list(
            response.context["customers"]
        )

        self.assertEqual(
            len(customers),
            2,
        )

        self.assertTrue(
            all(customer.is_active for customer in customers)
        )

    # ========================================================
    # TEST 05 — CUSTOMER TYPE FILTER
    # ========================================================

    def test_wholesale_customer_filter(self):

        response = self.client.get(
            reverse("customers:list"),
            {"type": "wholesale"},
        )

        customers = list(
            response.context["customers"]
        )

        self.assertEqual(
            len(customers),
            1,
        )

        self.assertEqual(
            customers[0].pk,
            self.wholesale_customer.pk,
        )

    # ========================================================
    # TEST 06 — BRANCH-SCOPED CUSTOMER STATISTICS
    # ========================================================

    def test_customer_list_financial_statistics(self):

        response = self.client.get(
            reverse("customers:list")
        )

        customer = next(
            row
            for row in response.context["customers"]
            if row.pk == self.customer.pk
        )

        # Only Branch A's sale should be included.
        self.assertEqual(
            customer.purchase_count,
            1,
        )

        self.assertEqual(
            customer.outstanding_total,
            Decimal("200.00"),
        )

    # ========================================================
    # TEST 07 — CUSTOMER FINANCIAL OVERVIEW
    # ========================================================

    def test_customer_detail_financial_summary(self):

        response = self.client.get(
            reverse(
                "customers:detail",
                args=[self.customer.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.context["total_purchases"],
            1,
        )

        self.assertEqual(
            response.context["total_spending"],
            Decimal("500.00"),
        )

        self.assertEqual(
            response.context["total_collected"],
            Decimal("300.00"),
        )

        self.assertEqual(
            response.context["total_outstanding"],
            Decimal("200.00"),
        )

    # ========================================================
    # TEST 08 — PAYMENT HISTORY BRANCH ISOLATION
    # ========================================================

    def test_payment_history_branch_restriction(self):

        response = self.client.get(
            reverse(
                "customers:detail",
                args=[self.customer.pk],
            )
        )

        payments = list(
            response.context["payments"]
        )

        self.assertEqual(
            len(payments),
            1,
        )

        self.assertEqual(
            payments[0].pk,
            self.payment_a.pk,
        )

        self.assertNotIn(
            self.payment_b.pk,
            [payment.pk for payment in payments],
        )

    # ========================================================
    # TEST 09 — LINK HISTORICAL INVOICE
    # ========================================================

    def test_link_historical_invoice(self):

        original_name = (
            self.unlinked_sale.customer_name
        )

        response = self.client.post(
            reverse(
                "customers:link_sale",
                args=[self.customer.pk],
            ),
            {
                "sale_id": str(
                    self.unlinked_sale.pk
                ),
                "invoice_confirmation": (
                    self.unlinked_sale.invoice_number
                ),
                "reason": (
                    "Original receipt and customer "
                    "contact details verified."
                ),
                "confirm": "yes",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.unlinked_sale.refresh_from_db()

        self.assertEqual(
            self.unlinked_sale.customer_id,
            self.customer.pk,
        )

        # Historical customer snapshot remains unchanged.
        self.assertEqual(
            self.unlinked_sale.customer_name,
            original_name,
        )

        self.assertTrue(
            CustomerSaleLinkAudit.objects.filter(
                sale=self.unlinked_sale,
                customer=self.customer,
                linked_by=self.admin,
            ).exists()
        )

    # ========================================================
    # TEST 10 — WRONG INVOICE CONFIRMATION
    # ========================================================

    def test_wrong_invoice_confirmation_rejected(self):

        response = self.client.post(
            reverse(
                "customers:link_sale",
                args=[self.customer.pk],
            ),
            {
                "sale_id": str(
                    self.unlinked_sale.pk
                ),
                "invoice_confirmation": (
                    "WRONG-INVOICE"
                ),
                "reason": (
                    "Testing invalid invoice number "
                    "confirmation rejection."
                ),
                "confirm": "yes",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.unlinked_sale.refresh_from_db()

        self.assertIsNone(
            self.unlinked_sale.customer_id
        )

        self.assertFalse(
            CustomerSaleLinkAudit.objects.filter(
                sale=self.unlinked_sale
            ).exists()
        )

    # ========================================================
    # TEST 11 — CROSS-BRANCH INVOICE LINKING
    # ========================================================

    def test_cross_branch_linking_rejected(self):

        other_branch_sale = Sale.objects.create(
            branch=self.branch_b,
            cashier=self.admin,
            customer=None,
            customer_name="Other Branch Customer",
            subtotal=Decimal("300.00"),
            total_amount=Decimal("300.00"),
            paid_amount=Decimal("300.00"),
            payment_status=Sale.PaymentStatus.PAID,
            status=Sale.Status.COMPLETED,
            completed_at=timezone.now(),
        )

        response = self.client.post(
            reverse(
                "customers:link_sale",
                args=[self.customer.pk],
            ),
            {
                "sale_id": str(
                    other_branch_sale.pk
                ),
                "invoice_confirmation": (
                    other_branch_sale.invoice_number
                ),
                "reason": (
                    "Testing cross-branch invoice "
                    "linking protection."
                ),
                "confirm": "yes",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        other_branch_sale.refresh_from_db()

        self.assertIsNone(
            other_branch_sale.customer_id
        )

        self.assertFalse(
            CustomerSaleLinkAudit.objects.filter(
                sale=other_branch_sale
            ).exists()
        )

    # ========================================================
    # TEST 12 — CUSTOMER STATUS TOGGLE
    # ========================================================

    def test_customer_status_toggle(self):

        self.assertTrue(
            self.customer.is_active
        )

        response = self.client.post(
            reverse(
                "customers:toggle_status",
                args=[self.customer.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.customer.refresh_from_db()

        self.assertFalse(
            self.customer.is_active
        )
