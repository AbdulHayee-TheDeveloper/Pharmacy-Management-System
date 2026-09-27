from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

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

    quantity = models.PositiveIntegerField(
        default=0,
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
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
    ordering = ["expiry_date", "batch_number"]

    constraints = [
        models.UniqueConstraint(
            fields=["medicine", "branch", "batch_number"],
            name="unique_medicine_branch_batch",
        ),
    ]

    indexes = [
        models.Index(
            fields=["medicine", "branch"],
        ),
        models.Index(
            fields=["expiry_date"],
        ),
        models.Index(
            fields=["branch", "expiry_date"],
        ),
    ]

def __str__(self):
    return f"{self.medicine} - {self.batch_number}"

@property
def is_expired(self):
    return self.expiry_date < timezone.localdate()

@property
def is_out_of_stock(self):
    return self.quantity == 0

@property
def is_low_stock(self):
    return (
        self.quantity > 0
        and self.quantity <= self.medicine.minimum_stock_level
    )
