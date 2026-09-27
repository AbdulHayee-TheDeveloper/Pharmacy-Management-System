from django import forms
from django.core.validators import MinValueValidator

from branches.models import Branch
from medicines.models import Category, Medicine

from .models import InventoryBatch


class InventoryEntryForm(forms.Form):
    ENTRY_CHOICES = (
        ("new", "New Medicine"),
        ("existing", "Existing Medicine"),
    )

    # ------------------------------------------------------------------
    # Entry Mode
    # ------------------------------------------------------------------

    entry_type = forms.ChoiceField(
        choices=ENTRY_CHOICES,
        widget=forms.RadioSelect(
            attrs={
                "class": "form-check-input",
            }
        ),
        initial="new",
    )

    # ------------------------------------------------------------------
    # Existing Medicine
    # ------------------------------------------------------------------

    medicine = forms.ModelChoiceField(
        queryset=Medicine.objects.filter(is_active=True).order_by("name"),
        required=False,
        widget=forms.HiddenInput(),
    )

    # ------------------------------------------------------------------
    # New Medicine Master Information
    # ------------------------------------------------------------------

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
        queryset=Category.objects.filter(is_active=True).order_by("name"),
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
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 1,
                "placeholder": "e.g. 10",
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

    # ------------------------------------------------------------------
    # Inventory / Batch Information
    # ------------------------------------------------------------------

    branch = forms.ModelChoiceField(
        queryset=Branch.objects.filter(is_active=True).order_by("name"),
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
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": 0,
                "placeholder": "e.g. 500",
            }
        ),
    )

    purchase_price = forms.DecimalField(
        required=True,
        min_value=0,
        max_digits=10,
        decimal_places=2,
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

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

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
            }

            for field_name, label in required_fields.items():
                if not cleaned_data.get(field_name):
                    self.add_error(
                        field_name,
                        f"{label} is required for a new medicine.",
                    )

            barcode = cleaned_data.get("barcode")

            if barcode and Medicine.objects.filter(
                barcode=barcode
            ).exists():
                self.add_error(
                    "barcode",
                    "A medicine with this barcode already exists.",
                )

            sku = cleaned_data.get("sku")

            if sku and Medicine.objects.filter(
                sku=sku
            ).exists():
                self.add_error(
                    "sku",
                    "A medicine with this SKU already exists.",
                )

        elif entry_type == "existing":
            if not medicine:
                self.add_error(
                    "medicine",
                    "Please select an existing medicine.",
                )

        purchase_price = cleaned_data.get("purchase_price")
        selling_price = cleaned_data.get("selling_price")

        if (
            purchase_price is not None
            and selling_price is not None
            and selling_price < purchase_price
        ):
            self.add_error(
                "selling_price",
                "Selling price cannot be lower than the purchase price.",
            )

        minimum_stock_level = cleaned_data.get(
            "minimum_stock_level"
        )

        reorder_level = cleaned_data.get("reorder_level")

        if (
            minimum_stock_level is not None
            and reorder_level is not None
            and reorder_level < minimum_stock_level
        ):
            self.add_error(
                "reorder_level",
                "Reorder level cannot be lower than the minimum stock level.",
            )

        return cleaned_data