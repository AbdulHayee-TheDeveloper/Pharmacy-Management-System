
from collections import defaultdict

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import F
from django.forms import (
    BaseFormSet,
    formset_factory,
)
from django.utils import timezone

from .models import PurchaseItem


# ============================================================
# RECEIVING HEADER FORM
# ============================================================

class PurchaseReceivingForm(forms.Form):

    supplier_delivery_note = forms.CharField(
        max_length=100,
        required=False,
        label="Supplier Delivery Note",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Delivery note / challan number",
                "autocomplete": "off",
            }
        ),
    )

    notes = forms.CharField(
        required=False,
        label="Receiving Notes",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional receiving remarks...",
            }
        ),
    )


# ============================================================
# RECEIVING ITEM FORM
# ============================================================

class PurchaseReceivingItemForm(forms.Form):

    purchase_item = forms.ModelChoiceField(
        queryset=PurchaseItem.objects.none(),
        label="Purchase Medicine",
        empty_label="Select Medicine",
        widget=forms.Select(
            attrs={
                "class": "form-select",
            }
        ),
    )

    batch_number = forms.CharField(
        max_length=100,
        label="Batch Number",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter batch number",
                "autocomplete": "off",
            }
        ),
    )

    expiry_date = forms.DateField(
        label="Expiry Date",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={
                "type": "date",
                "class": "form-control",
            }
        ),
    )

    received_packs = forms.IntegerField(
        min_value=1,
        label="Received Packs",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "step": "1",
                "placeholder": "Packs",
            }
        ),
    )

    def __init__(self, *args, purchase=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.purchase = purchase

        if purchase is None:
            self.fields["purchase_item"].queryset = (
                PurchaseItem.objects.none()
            )
            return

        # Only medicines with unreceived packs
        # can be selected.
        remaining_items = (
            PurchaseItem.objects
            .filter(
                purchase=purchase,
                ordered_packs__gt=F("received_packs"),
            )
            .select_related("medicine")
            .order_by("medicine__name", "pk")
        )

        self.fields["purchase_item"].queryset = (
            remaining_items
        )

        # Meaningful option labels in the dropdown.
        self.fields[
            "purchase_item"
        ].label_from_instance = (
            lambda item: (
                f"{item.medicine.name} "
                f"— {item.remaining_packs} "
                f"pack(s) remaining"
            )
        )

    def clean_batch_number(self):
        batch_number = self.cleaned_data[
            "batch_number"
        ].strip()

        if not batch_number:
            raise ValidationError(
                "Batch number is required."
            )

        return batch_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data[
            "expiry_date"
        ]

        if expiry_date <= timezone.localdate():
            raise ValidationError(
                "Expiry date must be in the future."
            )

        return expiry_date

    def clean(self):
        cleaned_data = super().clean()

        purchase_item = cleaned_data.get(
            "purchase_item"
        )

        received_packs = cleaned_data.get(
            "received_packs"
        )

        if (
            purchase_item is not None
            and self.purchase is not None
            and purchase_item.purchase_id != self.purchase.pk
        ):
            self.add_error(
                "purchase_item",
                "This medicine does not belong "
                "to the selected purchase.",
            )

        if (
            purchase_item is not None
            and received_packs is not None
            and received_packs > purchase_item.remaining_packs
        ):
            self.add_error(
                "received_packs",
                (
                    f"Only {purchase_item.remaining_packs} "
                    "pack(s) are remaining."
                ),
            )

        return cleaned_data


# ============================================================
# RECEIVING FORMSET VALIDATION
# ============================================================

class BasePurchaseReceivingFormSet(BaseFormSet):

    def __init__(self, *args, purchase=None, **kwargs):
        self.purchase = purchase
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)

        kwargs["purchase"] = self.purchase

        return kwargs

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        if self.purchase is None:
            raise ValidationError(
                "A purchase order is required."
            )

        total_by_purchase_item = defaultdict(int)
        seen_batches = set()
        valid_rows = 0

        for form in self.forms:

            if not form.cleaned_data:
                continue

            if form.cleaned_data.get("DELETE"):
                continue

            purchase_item = form.cleaned_data.get(
                "purchase_item"
            )

            batch_number = form.cleaned_data.get(
                "batch_number"
            )

            received_packs = form.cleaned_data.get(
                "received_packs"
            )

            if (
                purchase_item is None
                or not batch_number
                or received_packs is None
            ):
                continue

            valid_rows += 1

            # Prevent the same medicine and batch
            # from being submitted twice.
            batch_key = (
                purchase_item.medicine_id,
                batch_number,
            )

            if batch_key in seen_batches:
                form.add_error(
                    "batch_number",
                    "This medicine and batch number "
                    "are already present in the delivery.",
                )
            else:
                seen_batches.add(batch_key)

            total_by_purchase_item[
                purchase_item.pk
            ] += received_packs

        if valid_rows < 1:
            raise ValidationError(
                "Add at least one medicine "
                "to receive."
            )

        # Multiple different batches of the same
        # medicine may be received together.
        #
        # Their combined quantity cannot exceed
        # the purchase item's remaining packs.
        remaining_items = {
            item.pk: item
            for item in PurchaseItem.objects.filter(
                purchase=self.purchase
            )
        }

        for purchase_item_id, total_packs in (
            total_by_purchase_item.items()
        ):
            item = remaining_items.get(
                purchase_item_id
            )

            if item is None:
                raise ValidationError(
                    "Invalid purchase medicine selected."
                )

            if total_packs > item.remaining_packs:
                raise ValidationError(
                    f"{item.medicine.name}: "
                    f"only {item.remaining_packs} pack(s) "
                    "remain, but the delivery contains "
                    f"{total_packs} pack(s)."
                )

    def get_receiving_items(self):
        """
        Convert validated formset rows into the
        format expected by receive_purchase_stock().

        Call only after is_valid() returns True.
        """
        if not self.is_valid():
            raise ValueError(
                "Cannot extract data from "
                "an invalid receiving formset."
            )

        items = []

        for form in self.forms:

            data = form.cleaned_data

            if not data or data.get("DELETE"):
                continue

            items.append({
                "purchase_item_id": (
                    data["purchase_item"].pk
                ),
                "batch_number": data["batch_number"],
                "expiry_date": data["expiry_date"],
                "received_packs": data["received_packs"],
            })

        return items


# ============================================================
# RECEIVING FORMSET FACTORY
# ============================================================

PurchaseReceivingItemFormSet = formset_factory(
    PurchaseReceivingItemForm,
    formset=BasePurchaseReceivingFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    max_num=100,
    validate_max=True,
)
