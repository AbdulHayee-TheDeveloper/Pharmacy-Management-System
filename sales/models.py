import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def generate_invoice_number():
    date_part = timezone.localdate().strftime("%Y%m%d")
    unique_part = uuid.uuid4().hex[:10].upper()

    return f"SALE-{date_part}-{unique_part}"


class Sale(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"
        VOID = "void", "Void"
        REFUNDED = "refunded", "Refunded"

    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        MOBILE_WALLET = "mobile_wallet", "Mobile Wallet"
        CREDIT = "credit", "Credit"
        MIXED = "mixed", "Mixed"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PARTIAL = "partial", "Partially Paid"
        PAID = "paid", "Paid"

    invoice_number = models.CharField(
        max_length=40,
        unique=True,
        default=generate_invoice_number,
        editable=False,
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="sales",
    )

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="processed_sales",
    )
    customer = models.ForeignKey(
    "customers.Customer",
    on_delete=models.PROTECT,
    related_name="sales",
    null=True,
    blank=True,
    db_index=True,
    help_text=(
        "Optional registered customer. "
        "Null means a walk-in or unlinked sale."
    ),
)
    customer_name = models.CharField(
        max_length=200,
        blank=True,
    )

    customer_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    change_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    notes = models.TextField(
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "branch",
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "status",
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "payment_status",
                    "created_at",
                ]
            ),
            models.Index(
                fields=[
                    "cashier",
                    "created_at",
                ]
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    subtotal__gte=0
                ),
                name=(
                    "sale_subtotal_non_negative"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    discount_amount__gte=0
                ),
                name=(
                    "sale_discount_non_negative"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    tax_amount__gte=0
                ),
                name=(
                    "sale_tax_non_negative"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    total_amount__gte=0
                ),
                name=(
                    "sale_total_non_negative"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    paid_amount__gte=0
                ),
                name=(
                    "sale_paid_non_negative"
                ),
            ),
            models.CheckConstraint(
                condition=Q(
                    change_amount__gte=0
                ),
                name=(
                    "sale_change_non_negative"
                ),
            ),
        ]

        permissions = [
            (
                "void_sale",
                "Can void completed sale",
            ),
            (
                "refund_sale",
                "Can refund sale",
            ),
        ]

    def __str__(self):
        return self.invoice_number


class SaleItem(models.Model):
    class SaleType(models.TextChoices):
        PACK = "pack", "Pack"
        UNIT = "unit", "Loose Unit"

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )

    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )

    inventory_batch = models.ForeignKey(
        "inventory.InventoryBatch",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )

    # ============================================================
    # HISTORICAL SNAPSHOTS
    # ============================================================

    medicine_name = models.CharField(
        max_length=200,
    )

    batch_number = models.CharField(
        max_length=100,
    )

    sale_type = models.CharField(
        max_length=10,
        choices=SaleType.choices,
        default=SaleType.PACK,
    )

    unit_label = models.CharField(
        max_length=50,
        default="Unit",
    )

    pack_size = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1)
        ],
    )

    # Quantity selected by cashier.
    #
    # Examples:
    # 2 packs -> quantity = 2
    # 3 tablets -> quantity = 3
    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ],
    )

    # Actual smallest units removed from inventory.
    #
    # Example:
    # quantity = 2 packs
    # pack_size = 10
    # stock_quantity = 20 tablets
    #
    # Loose:
    # quantity = 3 tablets
    # stock_quantity = 3
    stock_quantity = models.PositiveIntegerField(
        default=1,
        validators=[
            MinValueValidator(1)
        ],
    )

    # Price of one selected sale unit.
    #
    # For pack sale:
    # unit_price = full pack price
    #
    # For loose sale:
    # unit_price = one tablet/capsule/etc price
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.00")
            )
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "id",
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(
                    quantity__gt=0
                ),
                name=(
                    "sale_item_quantity_positive"
                ),
            ),

            models.CheckConstraint(
                condition=Q(
                    stock_quantity__gt=0
                ),
                name=(
                    "sale_item_stock_quantity_positive"
                ),
            ),

            models.CheckConstraint(
                condition=Q(
                    pack_size__gt=0
                ),
                name=(
                    "sale_item_pack_size_positive"
                ),
            ),

            models.UniqueConstraint(
                fields=[
                    "sale",
                    "inventory_batch",
                    "sale_type",
                ],
                name=(
                    "unique_batch_sale_type_per_sale"
                ),
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "sale",
                    "medicine",
                ]
            ),
            models.Index(
                fields=[
                    "inventory_batch",
                ]
            ),
            models.Index(
                fields=[
                    "sale",
                    "sale_type",
                ]
            ),
        ]

    @property
    def sale_unit_display(self):
        if self.sale_type == self.SaleType.PACK:
            return "Pack"

        return self.unit_label

    @property
    def quantity_display(self):
        label = self.sale_unit_display

        if self.quantity == 1:
            return f"1 {label}"

        return f"{self.quantity} {label}s"

    def __str__(self):
        return (
            f"{self.sale.invoice_number} - "
            f"{self.medicine_name}"
        )


class SalePayment(models.Model):
    """
    Additional payment received against a completed sale.

    Original checkout payment remains stored in Sale.
    Subsequent payments are recorded here.
    """

    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.PROTECT,
        related_name="additional_payments",
    )

    payment_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.01"))
        ],
    )

    payment_method = models.CharField(
        max_length=30,
        choices=[
            ("cash", "Cash"),
            ("card", "Card"),
            ("bank_transfer", "Bank Transfer"),
            ("mobile_wallet", "Mobile Wallet"),
        ],
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
    )

    notes = models.TextField(blank=True)

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_sale_payments",
    )

    received_at = models.DateTimeField(
        default=timezone.now,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-received_at", "-pk"]

        indexes = [
            models.Index(
                fields=["sale", "received_at"]
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=Q(amount__gt=0),
                name="sale_payment_positive_amount",
            ),
        ]

    def __str__(self):
        return (
            self.payment_number
            or f"Payment #{self.pk}"
        )

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        super().save(*args, **kwargs)

        if is_new and not self.payment_number:
            number = f"PAY-{self.pk:06d}"

            type(self).objects.filter(
                pk=self.pk,
                payment_number__isnull=True,
            ).update(
                payment_number=number
            )

            self.payment_number = number
