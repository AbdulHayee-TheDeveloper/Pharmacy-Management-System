
from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet, inlineformset_factory

from branches.models import Branch
from medicines.models import Medicine
from suppliers.models import Supplier

from .models import Purchase, PurchaseItem


ZERO = Decimal("0.00")


# ============================================================
# COMMON FORM STYLING
# ============================================================

def apply_bootstrap_classes(form):
    for name, field in form.fields.items():
        widget = field.widget

        if isinstance(widget, forms.CheckboxInput):
            css_class = "form-check-input"

        elif isinstance(widget, forms.HiddenInput):
            continue

        elif isinstance(widget, forms.Select):
            css_class = "form-select"

        else:
            css_class = "form-control"

        existing = widget.attrs.get("class", "")

        widget.attrs["class"] = (
            f"{existing} {css_class}"
        ).strip()


# ============================================================
# PURCHASE HEADER FORM
# ============================================================

class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase

        fields = [
            "supplier",
            "branch",
            "purchase_date",
            "expected_delivery_date",
            "supplier_invoice_number",
            "notes",
        ]

        widgets = {
            "purchase_date": forms.DateInput(
                attrs={
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),

            "expected_delivery_date": forms.DateInput(
                attrs={
                    "type": "date",
                },
                format="%Y-%m-%d",
            ),

            "supplier_invoice_number": forms.TextInput(
                attrs={
                    "placeholder": "Supplier invoice number",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Additional purchase notes...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_bootstrap_classes(self)

        self.fields["supplier"].queryset = (
            Supplier.objects.filter(
                is_active=True
            ).order_by("name")
        )

        self.fields["supplier"].empty_label = (
            "Select Supplier"
        )

        self.fields["branch"].queryset = (
            Branch.objects.all().order_by("pk")
        )

        self.fields["branch"].empty_label = (
            "Select Branch"
        )

        self.fields["purchase_date"].input_formats = [
            "%Y-%m-%d"
        ]

        self.fields[
            "expected_delivery_date"
        ].input_formats = [
            "%Y-%m-%d"
        ]

        if self.instance.pk:
            # Existing inactive suppliers remain selectable
            # for their historical purchase records.
            self.fields["supplier"].queryset = (
                Supplier.objects.filter(
                    is_active=True
                )
                | Supplier.objects.filter(
                    pk=self.instance.supplier_id
                )
            ).distinct().order_by("name")

    def clean(self):
        cleaned_data = super().clean()

        purchase_date = cleaned_data.get(
            "purchase_date"
        )

        delivery_date = cleaned_data.get(
            "expected_delivery_date"
        )

        if (
            purchase_date
            and delivery_date
            and delivery_date < purchase_date
        ):
            self.add_error(
                "expected_delivery_date",
                "Expected delivery date cannot be "
                "earlier than purchase date.",
            )

        return cleaned_data


# ============================================================
# PURCHASE ITEM FORM
# ============================================================

class PurchaseItemForm(forms.ModelForm):

    class Meta:
        model = PurchaseItem

        fields = [
            "medicine",
            "ordered_packs",
            "purchase_price",
            "selling_price",
            "discount_amount",
            "notes",
        ]

        widgets = {
            "ordered_packs": forms.NumberInput(
                attrs={
                    "min": 1,
                    "step": 1,
                    "placeholder": "Packs",
                }
            ),

            "purchase_price": forms.NumberInput(
                attrs={
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "Purchase price / pack",
                }
            ),

            "selling_price": forms.NumberInput(
                attrs={
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "Selling price / pack",
                }
            ),

            "discount_amount": forms.NumberInput(
                attrs={
                    "min": 0,
                    "step": "0.01",
                    "placeholder": "Discount",
                }
            ),

            "notes": forms.TextInput(
                attrs={
                    "placeholder": "Optional item notes",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_bootstrap_classes(self)

        self.fields["medicine"].queryset = (
            Medicine.objects.filter(
                is_active=True
            ).order_by("name", "pk")
        )

        self.fields["medicine"].empty_label = (
            "Select Medicine"
        )

        self.fields["ordered_packs"].min_value = 1

        self.fields["purchase_price"].min_value = ZERO
        self.fields["selling_price"].min_value = ZERO
        self.fields["discount_amount"].min_value = ZERO

        self.fields["discount_amount"].required = False

        if self.instance.pk:
            # Existing medicine can still be displayed
            # if it was made inactive later.
            self.fields["medicine"].queryset = (
                Medicine.objects.filter(
                    is_active=True
                )
                | Medicine.objects.filter(
                    pk=self.instance.medicine_id
                )
            ).distinct().order_by("name", "pk")

            if self.instance.received_packs > 0:
                # Received lines must be handled by the
                # purchase receiving/editing workflow.
                for field_name in [
                    "medicine",
                    "ordered_packs",
                    "purchase_price",
                    "selling_price",
                    "discount_amount",
                ]:
                    self.fields[field_name].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        medicine = cleaned_data.get("medicine")
        ordered_packs = cleaned_data.get(
            "ordered_packs"
        )
        purchase_price = cleaned_data.get(
            "purchase_price"
        )
        selling_price = cleaned_data.get(
            "selling_price"
        )
        discount_amount = (
            cleaned_data.get("discount_amount")
            or ZERO
        )

        cleaned_data["discount_amount"] = (
            discount_amount
        )

        if medicine and medicine.pack_size < 1:
            self.add_error(
                "medicine",
                "Selected medicine has an invalid pack size.",
            )

        if (
            ordered_packs is not None
            and purchase_price is not None
        ):
            gross_total = (
                Decimal(ordered_packs)
                * purchase_price
            )

            if discount_amount > gross_total:
                self.add_error(
                    "discount_amount",
                    "Discount cannot exceed the "
                    "item's gross amount.",
                )

        if (
            purchase_price is not None
            and selling_price is not None
            and selling_price < purchase_price
        ):
            self.add_error(
                "selling_price",
                "Selling price cannot be lower "
                "than purchase price.",
            )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Snapshot pack size when the item is first created.
        # Never trust a hidden field for this value.
        if not instance.pk:
            if instance.medicine_id:
                instance.pack_size = (
                    instance.medicine.pack_size
                )

            instance.received_packs = 0

        if commit:
            instance.save()
            self.save_m2m()

        return instance


# ============================================================
# PURCHASE ITEM FORMSET VALIDATION
# ============================================================

class BasePurchaseItemFormSet(BaseInlineFormSet):

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        seen_medicines = set()
        valid_items = 0

        for form in self.forms:

            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            medicine = form.cleaned_data.get(
                "medicine"
            )

            if medicine is None:
                continue

            valid_items += 1

            if medicine.pk in seen_medicines:
                form.add_error(
                    "medicine",
                    "This medicine is already "
                    "added to the purchase.",
                )
                continue

            seen_medicines.add(medicine.pk)

        if valid_items < 1:
            raise ValidationError(
                "Add at least one medicine "
                "to the purchase order."
            )


# ============================================================
# INLINE FORMSET
# ============================================================

PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    form=PurchaseItemForm,
    formset=BasePurchaseItemFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
