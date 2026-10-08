
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


ZERO = Decimal("0.00")


class Purchase(models.Model):

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ORDERED = "ordered", "Ordered"
        PARTIALLY_RECEIVED = (
            "partially_received",
            "Partially Received",
        )
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    purchase_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    supplier = models.ForeignKey(
        "suppliers.Supplier",
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    purchase_date = models.DateField(
        default=timezone.localdate,
    )

    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
    )

    supplier_invoice_number = models.CharField(
        max_length=100,
        blank=True,
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    subtotal = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    discount_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    tax_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    notes = models.TextField(
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchases",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at", "-pk"]

        indexes = [
            models.Index(
                fields=["branch", "status"],
            ),
            models.Index(
                fields=["supplier", "purchase_date"],
            ),
            models.Index(
                fields=["-purchase_date"],
            ),
        ]

    def __str__(self):
        return self.purchase_number or f"Purchase #{self.pk}"

    def clean(self):
        super().clean()

        if (
            self.expected_delivery_date
            and self.purchase_date
            and self.expected_delivery_date < self.purchase_date
        ):
            raise ValidationError({
                "expected_delivery_date": (
                    "Expected delivery date cannot be "
                    "earlier than purchase date."
                )
            })

        if self.pk:
            old_purchase = type(self).objects.filter(
                pk=self.pk,
            ).first()

            if old_purchase:
                if old_purchase.supplier_id != self.supplier_id:
                    if self.items.exists():
                        raise ValidationError({
                            "supplier": (
                                "Supplier cannot be changed "
                                "after purchase items are added."
                            )
                        })

                if old_purchase.branch_id != self.branch_id:
                    if self.items.filter(
                        received_packs__gt=0
                    ).exists():
                        raise ValidationError({
                            "branch": (
                                "Branch cannot be changed "
                                "after stock has been received."
                            )
                        })

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        super().save(*args, **kwargs)

        if is_new and not self.purchase_number:
            generated_number = f"PUR-{self.pk:06d}"

            type(self).objects.filter(
                pk=self.pk,
                purchase_number__isnull=True,
            ).update(
                purchase_number=generated_number,
            )

            self.purchase_number = generated_number

    @property
    def calculated_total(self):
        return (
            self.subtotal
            - self.discount_amount
            + self.tax_amount
        )

    @property
    def total_ordered_packs(self):
        return sum(
            item.ordered_packs
            for item in self.items.all()
        )

    @property
    def total_received_packs(self):
        return sum(
            item.received_packs
            for item in self.items.all()
        )


class PurchaseItem(models.Model):

    purchase = models.ForeignKey(
        "purchases.Purchase",
        on_delete=models.CASCADE,
        related_name="items",
    )

    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )

    ordered_packs = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    received_packs = models.PositiveIntegerField(
        default=0,
    )

    pack_size = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=(
            "Units per pack at the time "
            "of purchase."
        ),
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        help_text="Purchase price per full pack.",
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(ZERO)],
        help_text="Expected selling price per full pack.",
    )

    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=ZERO,
        validators=[MinValueValidator(ZERO)],
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["pk"]

        indexes = [
            models.Index(
                fields=["purchase", "medicine"],
            ),
        ]

    def __str__(self):
        return (
            f"{self.medicine} - "
            f"{self.ordered_packs} packs"
        )

    def clean(self):
        super().clean()

        if (
            self.ordered_packs is not None
            and self.received_packs is not None
            and self.received_packs > self.ordered_packs
        ):
            raise ValidationError({
                "received_packs": (
                    "Received packs cannot exceed "
                    "ordered packs."
                )
            })

        if (
            self.ordered_packs is not None
            and self.purchase_price is not None
            and self.discount_amount is not None
        ):
            gross_total = (
                Decimal(self.ordered_packs)
                * self.purchase_price
            )

            if self.discount_amount > gross_total:
                raise ValidationError({
                    "discount_amount": (
                        "Discount cannot exceed "
                        "the item total."
                    )
                })

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.filter(
                pk=self.pk,
            ).first()

            if previous:
                if (
                    previous.received_packs
                    > self.received_packs
                ):
                    raise ValidationError(
                        "Received quantity cannot be reduced."
                    )

                if previous.received_packs > 0:
                    protected_fields = (
                        "purchase_id",
                        "medicine_id",
                        "pack_size",
                    )

                    for field in protected_fields:
                        if (
                            getattr(previous, field)
                            != getattr(self, field)
                        ):
                            raise ValidationError(
                                "Cannot change medicine, "
                                "purchase or pack size after "
                                "stock has been received."
                            )

        self.full_clean()

        gross_total = (
            Decimal(self.ordered_packs)
            * self.purchase_price
        )

        self.line_total = (
            gross_total - self.discount_amount
        )

        super().save(*args, **kwargs)

    @property
    def remaining_packs(self):
        return max(
            self.ordered_packs - self.received_packs,
            0,
        )

    @property
    def ordered_units(self):
        return self.ordered_packs * self.pack_size

    @property
    def received_units(self):
        return self.received_packs * self.pack_size

    @property
    def is_fully_received(self):
        return (
            self.received_packs >= self.ordered_packs
        )

# ============================================================
# PHASE 7.8.1 — PURCHASE STOCK RECEIVING
# ============================================================


class PurchaseReceipt(models.Model):
    """
    One stock delivery received against a purchase order.

    A single purchase may have multiple receipts because
    suppliers can deliver stock in separate shipments.

    Receipt posting and inventory changes will be handled
    together in the stock receiving service.
    """

    purchase = models.ForeignKey(
        "purchases.Purchase",
        on_delete=models.PROTECT,
        related_name="receipts",
    )

    receipt_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    received_at = models.DateTimeField(
        default=timezone.now,
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="purchase_receipts",
    )

    supplier_delivery_note = models.CharField(
        max_length=100,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-received_at", "-pk"]

        indexes = [
            models.Index(
                fields=["purchase", "received_at"],
            ),
        ]

    def __str__(self):
        return (
            self.receipt_number
            or f"Receipt #{self.pk}"
        )

    def clean(self):
        super().clean()

        if not self.purchase_id:
            return

        allowed_statuses = {
            Purchase.Status.ORDERED,
            Purchase.Status.PARTIALLY_RECEIVED,
            Purchase.Status.RECEIVED,
        }

        if self.purchase.status not in allowed_statuses:
            raise ValidationError({
                "purchase": (
                    "Stock receipts are only permitted "
                    "for ordered purchases."
                )
            })

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        super().save(*args, **kwargs)

        if is_new and not self.receipt_number:
            generated_number = (
                f"REC-{self.pk:06d}"
            )

            type(self).objects.filter(
                pk=self.pk,
                receipt_number__isnull=True,
            ).update(
                receipt_number=generated_number
            )

            self.receipt_number = generated_number

    @property
    def total_received_packs(self):
        return sum(
            item.received_packs
            for item in self.items.all()
        )


class PurchaseReceiptItem(models.Model):
    """
    One medicine batch in a supplier delivery.

    Different batches of the same medicine may be
    recorded as separate receipt items.
    """

    receipt = models.ForeignKey(
        "purchases.PurchaseReceipt",
        on_delete=models.PROTECT,
        related_name="items",
    )

    purchase_item = models.ForeignKey(
        "purchases.PurchaseItem",
        on_delete=models.PROTECT,
        related_name="receipt_items",
    )

    batch_number = models.CharField(
        max_length=100,
    )

    expiry_date = models.DateField()

    received_packs = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ],
    )

    pack_size = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1)
        ],
        help_text=(
            "Snapshot of units per pack "
            "when stock was received."
        ),
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
        help_text="Cost per full pack.",
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
        help_text="Selling price per full pack.",
    )

    inventory_batch = models.ForeignKey(
        "inventory.InventoryBatch",
        on_delete=models.PROTECT,
        related_name="purchase_receipt_items",
        null=True,
        blank=True,
        editable=False,
        help_text=(
            "Inventory batch updated or created "
            "during receipt posting."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["pk"]

        indexes = [
            models.Index(
                fields=[
                    "purchase_item",
                    "batch_number",
                ]
            ),
        ]

    def __str__(self):
        return (
            f"{self.purchase_item.medicine} "
            f"| Batch {self.batch_number} "
            f"| {self.received_packs} packs"
        )

    def clean(self):
        super().clean()

        if (
            self.receipt_id
            and self.purchase_item_id
        ):
            if (
                self.receipt.purchase_id
                != self.purchase_item.purchase_id
            ):
                raise ValidationError(
                    "The received medicine must belong "
                    "to the same purchase order."
                )

        if self.batch_number:
            self.batch_number = (
                self.batch_number.strip()
            )

            if not self.batch_number:
                raise ValidationError({
                    "batch_number": (
                        "Batch number is required."
                    )
                })

        if (
            self.expiry_date
            and self.expiry_date <= timezone.localdate()
        ):
            raise ValidationError({
                "expiry_date": (
                    "Expired medicines cannot "
                    "be received into stock."
                )
            })

        if (
            self.purchase_item_id
            and self.pack_size
        ):
            if (
                self.pack_size
                != self.purchase_item.pack_size
            ):
                raise ValidationError({
                    "pack_size": (
                        "Pack size must match the "
                        "original purchase item."
                    )
                })

        if (
            self.inventory_batch_id
            and self.purchase_item_id
        ):
            inventory_batch = self.inventory_batch

            if (
                inventory_batch.medicine_id
                != self.purchase_item.medicine_id
                or inventory_batch.branch_id
                != self.purchase_item.purchase.branch_id
                or inventory_batch.batch_number
                != self.batch_number
            ):
                raise ValidationError({
                    "inventory_batch": (
                        "Inventory batch does not match "
                        "the purchase medicine, branch "
                        "or batch number."
                    )
                })

    @property
    def received_units(self):
        return (
            self.received_packs
            * self.pack_size
        )

    @property
    def received_value(self):
        return (
            Decimal(self.received_packs)
            * self.purchase_price
        )
