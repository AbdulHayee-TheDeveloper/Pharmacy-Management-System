
from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Supplier(models.Model):
    supplier_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
    )

    name = models.CharField(max_length=150)

    company_name = models.CharField(
        max_length=200,
        blank=True,
    )

    contact_person = models.CharField(
        max_length=150,
        blank=True,
    )

    phone = models.CharField(max_length=20)

    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(blank=True)

    ntn = models.CharField(
        max_length=30,
        blank=True,
    )

    address = models.TextField(blank=True)

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00"))
        ],
        help_text="Initial payable balance in PKR.",
    )

    is_active = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"

    def __str__(self):
        if self.company_name:
            return f"{self.name} - {self.company_name}"
        return self.name

    def save(self, *args, **kwargs):
        if self.pk is None:
            super().save(*args, **kwargs)

            self.supplier_code = f"SUP-{self.pk:04d}"

            super().save(
                update_fields=["supplier_code"]
            )
        else:
            super().save(*args, **kwargs)
