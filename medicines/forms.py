from django import forms

from .models import Category, Medicine


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category

        fields = [
            "name",
            "description",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Antibiotics",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional category description",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine

        fields = [
            "name",
            "generic_name",
            "category",
            "manufacturer",
            "country_of_origin",
            "dosage_form",
            "strength",
            "unit",
            "pack_size",
            "allow_loose_sale",
            "barcode",
            "sku",
            "purchase_price",
            "selling_price",
            "tax_rate",
            "minimum_stock_level",
            "reorder_level",
            "prescription_required",
            "controlled_medicine",
            "storage_condition",
            "description",
            "image",
            "is_active",
            "use_pharmacy_default_tax",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Panadol",
                }
            ),
            "generic_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Paracetamol",
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "manufacturer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. GSK",
                }
            ),
            "country_of_origin": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Pakistan",
                }
            ),
            "dosage_form": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "strength": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 500mg",
                }
            ),
            "unit": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "pack_size": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "e.g. 20",
                }
            ),
            "allow_loose_sale": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "barcode": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Scan or enter barcode",
                }
            ),
            "sku": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Internal SKU",
                }
            ),
            "purchase_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "selling_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "tax_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "max": 100,
                    "step": "0.01",
                    "placeholder": "0.00",
                }
            ),
            "minimum_stock_level": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "placeholder": "e.g. 10",
                }
            ),
            "reorder_level": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 0,
                    "placeholder": "e.g. 20",
                }
            ),
            "prescription_required": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "controlled_medicine": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "storage_condition": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Store below 25°C",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Additional medicine information...",
                }
            ),
            "image": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "use_pharmacy_default_tax": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

        labels = {
            "name": "Brand Name",
            "generic_name": "Generic Name",
            "country_of_origin": "Country of Origin",
            "dosage_form": "Dosage Form",
            "unit": "Smallest Sellable Unit",
            "pack_size": "Units Per Pack",
            "allow_loose_sale": "Allow Loose Sale",
            "purchase_price": "Default Purchase Price",
            "selling_price": "Default Selling Price",
            "tax_rate": "Tax Rate (%)",
            "minimum_stock_level": "Minimum Stock Level",
            "reorder_level": "Reorder Level",
            "prescription_required": "Prescription Required",
            "controlled_medicine": "Controlled Medicine",
            "storage_condition": "Storage Condition",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = Category.objects.filter(
            is_active=True
        ).order_by("name")

        self.has_inventory_batches = False

        if self.instance and self.instance.pk:
            self.has_inventory_batches = (
                self.instance.inventory_batches.exists()
            )

        if self.has_inventory_batches:
            self.fields["unit"].disabled = True
            self.fields["pack_size"].disabled = True

            self.fields["unit"].help_text = (
                "This field cannot be changed because stock batches "
                "already exist for this medicine."
            )

            self.fields["pack_size"].help_text = (
                "This field cannot be changed because stock batches "
                "already exist for this medicine."
            )

    def clean(self):
        cleaned_data = super().clean()

        purchase_price = cleaned_data.get("purchase_price")
        selling_price = cleaned_data.get("selling_price")

        minimum_stock = cleaned_data.get("minimum_stock_level")
        reorder_level = cleaned_data.get("reorder_level")

        pack_size = cleaned_data.get("pack_size")
        allow_loose_sale = cleaned_data.get("allow_loose_sale")

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

        if (
            minimum_stock is not None
            and reorder_level is not None
            and reorder_level < minimum_stock
        ):
            self.add_error(
                "reorder_level",
                (
                    "Reorder level should be equal to or greater "
                    "than the minimum stock level."
                ),
            )

        if (
            allow_loose_sale
            and pack_size is not None
            and pack_size <= 1
        ):
            self.add_error(
                "pack_size",
                (
                    "Pack size must be greater than 1 "
                    "when loose sale is enabled."
                ),
            )

        return cleaned_data