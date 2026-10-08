
from django import forms

from .models import Supplier


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier

        fields = [
            "name",
            "company_name",
            "contact_person",
            "phone",
            "alternate_phone",
            "email",
            "ntn",
            "address",
            "city",
            "opening_balance",
            "is_active",
            "notes",
        ]

        widgets = {
            "address": forms.Textarea(
                attrs={"rows": 3}
            ),
            "notes": forms.Textarea(
                attrs={"rows": 3}
            ),
            "opening_balance": forms.NumberInput(
                attrs={
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }

        labels = {
            "name": "Supplier Name",
            "ntn": "NTN / Tax Number",
            "opening_balance": "Opening Payable Balance (PKR)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if isinstance(
                field.widget,
                forms.CheckboxInput,
            ):
                field.widget.attrs["class"] = (
                    "form-check-input"
                )
            else:
                field.widget.attrs["class"] = (
                    "form-control"
                )

        self.fields["name"].widget.attrs[
            "placeholder"
        ] = "e.g. Ahmed Pharma Distributors"

        self.fields["company_name"].widget.attrs[
            "placeholder"
        ] = "Registered company name"

        self.fields["contact_person"].widget.attrs[
            "placeholder"
        ] = "Contact person name"

        self.fields["phone"].widget.attrs[
            "placeholder"
        ] = "e.g. 03001234567"

        self.fields["alternate_phone"].widget.attrs[
            "placeholder"
        ] = "Optional alternate number"

        self.fields["email"].widget.attrs[
            "placeholder"
        ] = "supplier@example.com"

        self.fields["city"].widget.attrs[
            "placeholder"
        ] = "e.g. Faisalabad"

        self.fields["opening_balance"].widget.attrs[
            "readonly"
        ] = True if self.instance.pk else False

        self.fields["opening_balance"].help_text = (
            "Initial historical payable amount. "
            "Cannot be edited after supplier creation."
        )

    def clean(self):
        cleaned_data = super().clean()

        for field_name in [
            "name",
            "company_name",
            "contact_person",
            "phone",
            "alternate_phone",
            "ntn",
            "city",
        ]:
            value = cleaned_data.get(field_name)

            if isinstance(value, str):
                cleaned_data[field_name] = value.strip()

        name = cleaned_data.get("name")
        phone = cleaned_data.get("phone")

        if name and len(name) < 3:
            self.add_error(
                "name",
                "Supplier name must contain at least 3 characters.",
            )

        if phone:
            normalized = phone.replace(
                " ", ""
            ).replace("-", "")

            if not (
                normalized.startswith("+")
                and normalized[1:].isdigit()
                or normalized.isdigit()
            ):
                self.add_error(
                    "phone",
                    "Enter a valid phone number.",
                )

        return cleaned_data
