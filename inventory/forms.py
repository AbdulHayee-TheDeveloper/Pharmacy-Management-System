from django import forms
from django.utils import timezone
from .models import InventoryBatch, StockAdjustment
from branches.models import Branch
from medicines.models import Category, Medicine


class InventoryEntryForm(forms.Form):
    ENTRY_CHOICES = (
        ("new", "New Medicine"),
        ("existing", "Existing Medicine"),
    )

    entry_type = forms.ChoiceField(
        choices=ENTRY_CHOICES,
        widget=forms.RadioSelect(
            attrs={
                "class": "form-check-input",
            }
        ),
        initial="new",
    )

    # ============================================================
    # Existing Medicine
    # ============================================================

    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.filter(
            is_active=True
        ).order_by("name"),
        required=False,
        widget=forms.HiddenInput(),
    )

    # ============================================================
    # New Medicine Master Information
    # ============================================================

    name = forms.CharField(
        max_length=200,
        required=False,
        label="Brand Name",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Panadol",
            }
        ),
    )

    generic_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Paracetamol",
            }
        ),
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(
            is_active=True
        ).order_by("name"),
        required=False,
        empty_label="Select category",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    manufacturer = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. GSK",
            }
        ),
    )

    country_of_origin = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Pakistan",
            }
        ),
    )

    dosage_form = forms.ChoiceField(
        choices=Medicine.DosageForm.choices,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    strength = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. 500mg",
            }
        ),
    )

    unit = forms.ChoiceField(
        choices=Medicine.Unit.choices,
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    pack_size = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        label="Units Per Pack",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "e.g. 10",
            }
        ),
    )

    allow_loose_sale = forms.BooleanField(
        required=False,
        label="Allow Loose Sale",
        help_text=(
            "Allow individual tablets, capsules or other units "
            "to be sold separately."
        ),
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    barcode = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optional",
            }
        ),
    )

    sku = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Optional",
            }
        ),
    )

    minimum_stock_level = forms.IntegerField(
        required=False,
        min_value=0,
        initial=10,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
                "placeholder": "e.g. 10",
            }
        ),
    )

    reorder_level = forms.IntegerField(
        required=False,
        min_value=0,
        initial=20,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
                "placeholder": "e.g. 20",
            }
        ),
    )

    prescription_required = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    controlled_medicine = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    storage_condition = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. Store below 25°C",
            }
        ),
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional medicine description",
            }
        ),
    )

    # ============================================================
    # Inventory / Batch Information
    # ============================================================

    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(
            is_active=True
        ).order_by("name"),
        required=True,
        empty_label="Select branch",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    batch_number = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "e.g. PAN-2026-001",
            }
        ),
    )

    expiry_date = forms.DateField(
        required=True,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    quantity = forms.IntegerField(
        required=True,
        min_value=1,
        label="Number of Packs",
        help_text=(
            "Enter the number of complete packs received."
        ),
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "e.g. 50 packs",
            }
        ),
    )

    purchase_price = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Purchase Price Per Pack",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )

    selling_price = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
        label="Selling Price Per Pack",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
                "step": "0.01",
                "placeholder": "0.00",
            }
        ),
    )

    is_active = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    # ============================================================
    # Validation
    # ============================================================

    def clean(self):
        cleaned_data = super().clean()

        entry_type = cleaned_data.get("entry_type")
        medicine = cleaned_data.get("medicine")

        if entry_type == "new":
            required_fields = {
                "name": "Brand Name",
                "category": "Category",
                "dosage_form": "Dosage Form",
                "unit": "Unit",
                "pack_size": "Units Per Pack",
            }

            for field_name, label in required_fields.items():
                if not cleaned_data.get(field_name):
                    self.add_error(
                        field_name,
                        f"{label} is required for a new medicine.",
                    )

            barcode = (
                cleaned_data.get("barcode") or ""
            ).strip()

            if barcode:
                cleaned_data["barcode"] = barcode

                if Medicine.objects.filter(
                    barcode=barcode
                ).exists():
                    self.add_error(
                        "barcode",
                        "A medicine with this barcode already exists.",
                    )
            else:
                cleaned_data["barcode"] = None

            sku = (
                cleaned_data.get("sku") or ""
            ).strip()

            if sku:
                cleaned_data["sku"] = sku

                if Medicine.objects.filter(
                    sku=sku
                ).exists():
                    self.add_error(
                        "sku",
                        "A medicine with this SKU already exists.",
                    )
            else:
                cleaned_data["sku"] = None

            pack_size = (
                cleaned_data.get("pack_size") or 1
            )

            allow_loose_sale = cleaned_data.get(
                "allow_loose_sale",
                False,
            )

            if (
                allow_loose_sale
                and pack_size <= 1
            ):
                self.add_error(
                    "pack_size",
                    (
                        "Units per pack must be greater than 1 "
                        "when loose sale is enabled."
                    ),
                )

        elif entry_type == "existing":
            if not medicine:
                self.add_error(
                    "medicine",
                    "Please select an existing medicine.",
                )

        purchase_price = cleaned_data.get(
            "purchase_price"
        )

        selling_price = cleaned_data.get(
            "selling_price"
        )

        if (
            purchase_price is not None
            and selling_price is not None
            and selling_price < purchase_price
        ):
            self.add_error(
                "selling_price",
                (
                    "Selling price cannot be lower than "
                    "the purchase price."
                ),
            )

        expiry_date = cleaned_data.get(
            "expiry_date"
        )

        if (
            expiry_date
            and expiry_date < timezone.localdate()
        ):
            self.add_error(
                "expiry_date",
                "Cannot add an already expired batch.",
            )

        if entry_type == "new":
            minimum_stock_level = cleaned_data.get(
                "minimum_stock_level"
            )

            reorder_level = cleaned_data.get(
                "reorder_level"
            )

            if (
                minimum_stock_level is not None
                and reorder_level is not None
                and reorder_level
                < minimum_stock_level
            ):
                self.add_error(
                    "reorder_level",
                    (
                        "Reorder level cannot be lower than "
                        "the minimum stock level."
                    ),
                )

        return cleaned_data

class InventoryBatchEditForm(forms.ModelForm):
    class Meta:
        model = InventoryBatch

        fields = [
            "batch_number",
            "expiry_date",
            "purchase_price",
            "selling_price",
            "is_active",
        ]

        widgets = {
            "batch_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. PAN-2026-001",
                }
            ),
            "expiry_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "purchase_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "selling_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

        labels = {
            "batch_number": "Batch Number",
            "expiry_date": "Expiry Date",
            "purchase_price": "Purchase Price Per Pack",
            "selling_price": "Selling Price Per Pack",
            "is_active": "Active Batch",
        }

    def clean(self):
        cleaned_data = super().clean()

        batch_number = (
            cleaned_data.get("batch_number") or ""
        ).strip()

        purchase_price = cleaned_data.get(
            "purchase_price"
        )

        selling_price = cleaned_data.get(
            "selling_price"
        )

        expiry_date = cleaned_data.get(
            "expiry_date"
        )

        if batch_number:
            cleaned_data["batch_number"] = batch_number

            duplicate_batch = InventoryBatch.objects.filter(
                medicine=self.instance.medicine,
                branch=self.instance.branch,
                batch_number=batch_number,
            ).exclude(
                pk=self.instance.pk
            )

            if duplicate_batch.exists():
                self.add_error(
                    "batch_number",
                    (
                        "This batch number already exists for "
                        "this medicine and branch."
                    ),
                )

        if (
            purchase_price is not None
            and selling_price is not None
            and selling_price < purchase_price
        ):
            self.add_error(
                "selling_price",
                (
                    "Selling price cannot be lower than "
                    "the purchase price."
                ),
            )

        # Existing expired batches are allowed to remain expired.
        # But a valid/future batch cannot be changed to an already
        # expired date accidentally.
        if (
            expiry_date
            and expiry_date < timezone.localdate()
            and self.instance
            and self.instance.pk
            and expiry_date != self.instance.expiry_date
        ):
            self.add_error(
                "expiry_date",
                (
                    "Expiry date cannot be changed to "
                    "a date that has already passed."
                ),
            )

        return cleaned_data

class StockAdjustmentForm(forms.Form):
    adjustment_type = forms.ChoiceField(
        choices=StockAdjustment.AdjustmentType.choices,
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    quantity = forms.IntegerField(
        min_value=1,
        label="Quantity",
        help_text=(
            "Enter quantity in the medicine's "
            "smallest sellable unit."
        ),
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "e.g. 5",
            }
        ),
    )

    reason = forms.CharField(
        max_length=255,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": (
                    "e.g. Damaged stock, physical stock correction..."
                ),
            }
        ),
    )

    def __init__(self, *args, batch=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.batch = batch

        if batch:
            self.fields["quantity"].help_text = (
                f"Enter quantity in "
                f"{batch.medicine.unit_label.lower()}(s). "
                f"Current stock: {batch.quantity}."
            )

    def clean(self):
        cleaned_data = super().clean()

        adjustment_type = cleaned_data.get(
            "adjustment_type"
        )

        quantity = cleaned_data.get(
            "quantity"
        )

        if not self.batch or not quantity:
            return cleaned_data

        if (
            adjustment_type
            == StockAdjustment.AdjustmentType.REMOVE
            and quantity > self.batch.quantity
        ):
            self.add_error(
                "quantity",
                (
                    "Cannot remove more stock than "
                    "the current available quantity."
                ),
            )

        if (
            adjustment_type
            == StockAdjustment.AdjustmentType.ADD
            and self.batch.is_expired
        ):
            self.add_error(
                "adjustment_type",
                (
                    "Stock cannot be added to an expired batch."
                ),
            )

        return cleaned_data