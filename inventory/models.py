from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from core_settings.operational import (
    get_operational_settings, effective_low_stock_threshold,
)


MONEY_PLACES = Decimal("0.01")


class InventoryBatch(models.Model):
    medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.PROTECT,
        related_name="inventory_batches",
    )

    branch = models.ForeignKey(
        "branches.Branch",
        on_delete=models.PROTECT,
        related_name="inventory_batches",
    )

    batch_number = models.CharField(
        max_length=100,
    )

    expiry_date = models.DateField()

    # IMPORTANT:
    # Quantity is stored in the smallest sellable unit.
    #
    # Example:
    # Medicine pack_size = 10 tablets
    # 5 packs received
    # Database quantity = 50 tablets
    quantity = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Stock quantity in the medicine's smallest sellable unit."
        ),
    )

    # Prices represent one COMPLETE PACK.
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Purchase price per full pack.",
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Selling price per full pack.",
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "expiry_date",
            "batch_number",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "medicine",
                    "branch",
                    "batch_number",
                ],
                name="unique_medicine_branch_batch",
            ),
        ]

        indexes = [
            models.Index(
                fields=[
                    "medicine",
                    "branch",
                ],
            ),
            models.Index(
                fields=[
                    "expiry_date",
                ],
            ),
            models.Index(
                fields=[
                    "branch",
                    "expiry_date",
                ],
            ),
        ]

    def __str__(self):
        return (
            f"{self.medicine} - "
            f"{self.batch_number}"
        )

    @property
    def pack_size(self):
        return max(
            self.medicine.pack_size,
            1,
        )

    @property
    def unit_purchase_price(self):
        return (
            self.purchase_price
            / Decimal(self.pack_size)
        ).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

    @property
    def unit_selling_price(self):
        return (
            self.selling_price
            / Decimal(self.pack_size)
        ).quantize(
            MONEY_PLACES,
            rounding=ROUND_HALF_UP,
        )

    @property
    def full_packs_available(self):
        return self.quantity // self.pack_size

    @property
    def loose_units_available(self):
        return self.quantity % self.pack_size

    @property
    def stock_display(self):
        if self.pack_size <= 1:
            return (
                f"{self.quantity} "
                f"{self.medicine.unit_label}"
            )

        full_packs = self.full_packs_available
        loose_units = self.loose_units_available

        parts = []

        if full_packs:
            parts.append(
                f"{full_packs} pack"
                f"{'s' if full_packs != 1 else ''}"
            )

        if loose_units:
            parts.append(
                f"{loose_units} "
                f"{self.medicine.unit_label.lower()}"
                f"{'s' if loose_units != 1 else ''}"
            )

        return ", ".join(parts) or "0"

    @property
    def is_expired(self):
        return (
            self.expiry_date
            < timezone.localdate()
        )

    @property
    def is_out_of_stock(self):
        return self.quantity == 0

    @property
    def is_low_stock(self):
        # List/dashboard querysets annotate this once in SQL, avoiding N+1 queries.
        threshold = getattr(self, "effective_low_stock_threshold", None)
        if threshold is None:
            options = get_operational_settings()
            threshold = effective_low_stock_threshold(
                self.medicine.minimum_stock_level,
                options["low_stock_threshold"],
            )
        return 0 < self.quantity <= threshold


class StockAdjustment(models.Model):
    class AdjustmentType(models.TextChoices):
        ADD = "add", "Add Stock"
        REMOVE = "remove", "Remove Stock"

    batch = models.ForeignKey(
        InventoryBatch,
        on_delete=models.PROTECT,
        related_name="adjustments",
    )

    adjustment_type = models.CharField(
        max_length=10,
        choices=AdjustmentType.choices,
    )

    # Quantity is always stored in the medicine's
    # smallest sellable unit.
    quantity = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
        ],
    )

    previous_quantity = models.PositiveIntegerField()

    resulting_quantity = models.PositiveIntegerField()

    reason = models.CharField(
        max_length=255,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_stock_adjustments",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        indexes = [
            models.Index(
                fields=[
                    "batch",
                    "created_at",
                ],
            ),
            models.Index(
                fields=[
                    "adjustment_type",
                    "created_at",
                ],
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="stock_adjustment_quantity_gt_zero",
            ),
        ]

    def __str__(self):
        return (
            f"{self.get_adjustment_type_display()} - "
            f"{self.batch.batch_number} - "
            f"{self.quantity}"
        )