
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import (
    FileExtensionValidator,
    MinValueValidator,
    MaxValueValidator,
)
from django.db import models


def validate_logo_size(value):
    """
    Maximum uploaded logo size: 2 MB.
    """

    max_size = 2 * 1024 * 1024

    if value.size > max_size:
        raise ValidationError(
            "Logo size must not exceed 2 MB."
        )


class PharmacyProfile(models.Model):
    """
    Global pharmacy/business configuration.

    Exactly one row is used:
    primary key = 1.

    Settings are global at this stage.
    Branch-specific details remain in
    the existing branches application.
    """

    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False,
    )

    name = models.CharField(
        max_length=150,
        default="PharmaCare",
    )

    tagline = models.CharField(
        max_length=200,
        blank=True,
        default="Pharmacy Management System",
    )

    logo = models.ImageField(
        upload_to="pharmacy/logos/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                ]
            ),
            validate_logo_size,
        ],
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    registration_number = models.CharField(
        max_length=100,
        blank=True,
    )

    currency_code = models.CharField(
        max_length=3,
        choices=[
            ("PKR", "Pakistani Rupee (PKR)"),
        ],
        default="PKR",
    )

    default_tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
    )

    low_stock_threshold = models.PositiveIntegerField(
        default=20,
        help_text=(
            "Default threshold in individual stock units."
        ),
    )

    expiry_alert_days = models.PositiveIntegerField(
        default=30,
        validators=[
            MaxValueValidator(365),
        ],
    )

    receipt_footer = models.CharField(
        max_length=250,
        blank=True,
        default="Thank you for shopping with us!",
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "Pharmacy Profile"
        verbose_name_plural = "Pharmacy Profile"

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()

        if self.pk != 1:
            raise ValidationError(
                "Only the global pharmacy profile is allowed."
            )

    def save(self, *args, **kwargs):
        self.pk = 1
        self.full_clean()
        return super().save(*args, **kwargs)

    @classmethod
    def get_profile(cls):
        
        profile, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "name": "PharmaCare",
            },
        )

        return profile
