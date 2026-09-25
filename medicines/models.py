from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Medicine Category"
        verbose_name_plural = "Medicine Categories"

    def __str__(self):
        return self.name


class Medicine(models.Model):
    class DosageForm(models.TextChoices):
        TABLET = "tablet", "Tablet"
        CAPSULE = "capsule", "Capsule"
        SYRUP = "syrup", "Syrup"
        SUSPENSION = "suspension", "Suspension"
        INJECTION = "injection", "Injection"
        CREAM = "cream", "Cream"
        OINTMENT = "ointment", "Ointment"
        DROPS = "drops", "Drops"
        INHALER = "inhaler", "Inhaler"
        POWDER = "powder", "Powder"
        GEL = "gel", "Gel"
        LOTION = "lotion", "Lotion"
        OTHER = "other", "Other"

    class Unit(models.TextChoices):
        TABLET = "tablet", "Tablet"
        CAPSULE = "capsule", "Capsule"
        BOTTLE = "bottle", "Bottle"
        TUBE = "tube", "Tube"
        PACK = "pack", "Pack"
        BOX = "box", "Box"
        VIAL = "vial", "Vial"
        AMPOULE = "ampoule", "Ampoule"
        PIECE = "piece", "Piece"

    name = models.CharField(
        max_length=200,
        verbose_name="Brand Name",
    )

    generic_name = models.CharField(
        max_length=200,
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="medicines",
    )

    manufacturer = models.CharField(
        max_length=200,
        blank=True,
    )

    country_of_origin = models.CharField(
        max_length=100,
        blank=True,
    )

    dosage_form = models.CharField(
        max_length=20,
        choices=DosageForm.choices,
        default=DosageForm.TABLET,
    )

    strength = models.CharField(
        max_length=100,
        blank=True,
        help_text="Example: 500mg or 10mg/5ml",
    )

    unit = models.CharField(
        max_length=20,
        choices=Unit.choices,
        default=Unit.TABLET,
    )

    pack_size = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    barcode = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )

    sku = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )

    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    minimum_stock_level = models.PositiveIntegerField(
        default=10,
    )

    reorder_level = models.PositiveIntegerField(
        default=20,
    )

    prescription_required = models.BooleanField(
        default=False,
    )

    controlled_medicine = models.BooleanField(
        default=False,
    )

    storage_condition = models.CharField(
        max_length=255,
        blank=True,
        help_text="Example: Store below 25°C.",
    )

    description = models.TextField(
        blank=True,
    )

    image = models.ImageField(
        upload_to="medicines/",
        blank=True,
        null=True,
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
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["generic_name"]),
            models.Index(fields=["barcode"]),
            models.Index(fields=["sku"]),
            models.Index(fields=["category", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} {self.strength}".strip()