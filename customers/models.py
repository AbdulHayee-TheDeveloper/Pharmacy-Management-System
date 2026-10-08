
from django.db import models
from django.core.exceptions import ValidationError


class Customer(models.Model):

    class CustomerType(models.TextChoices):
        REGULAR = "regular", "Regular"
        WHOLESALE = "wholesale", "Wholesale"

    customer_code = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        null=True,
        blank=True,
    )

    name = models.CharField(max_length=150)

    phone = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
    )

    alternate_phone = models.CharField(
        max_length=20,
        blank=True,
    )

    email = models.EmailField(blank=True)

    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.REGULAR,
    )

    address = models.TextField(blank=True)

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    notes = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name", "pk"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["customer_type", "is_active"]),
        ]

    def __str__(self):
        return f"{self.customer_code or 'New'} - {self.name}"

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        self.phone = (self.phone or "").strip()

        if not self.name:
            raise ValidationError({
                "name": "Customer name is required."
            })

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new and not self.customer_code:
            super().save(*args, **kwargs)

            code = f"CUS-{self.pk:06d}"

            type(self).objects.filter(
                pk=self.pk
            ).update(customer_code=code)

            self.customer_code = code
        else:
            super().save(*args, **kwargs)

from django.conf import settings


class CustomerSaleLinkAudit(models.Model):
    """
    Permanent record of historical sale/customer linking.
    """

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="sale_link_audits",
    )

    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.PROTECT,
        related_name="customer_link_audits",
    )

    linked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="customer_sale_links",
    )

    reason = models.TextField()

    linked_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-linked_at", "-pk"]

    def __str__(self):
        return (
            f"{self.sale.invoice_number} "
            f"→ {self.customer.customer_code}"
        )
