
from django import forms

from .models import Customer


class CustomerForm(forms.ModelForm):

    class Meta:
        model = Customer

        fields = [
            "name",
            "phone",
            "alternate_phone",
            "email",
            "customer_type",
            "address",
            "city",
            "notes",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Customer full name",
                "autocomplete": "name",
            }),

            "phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "03XXXXXXXXX",
                "autocomplete": "tel",
            }),

            "alternate_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Alternate contact number",
            }),

            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "customer@example.com",
            }),

            "customer_type": forms.Select(attrs={
                "class": "form-select",
            }),

            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Customer address",
            }),

            "city": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "City",
            }),

            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional information",
            }),

            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def clean_name(self):
        value = self.cleaned_data["name"].strip()

        if len(value) < 2:
            raise forms.ValidationError(
                "Enter at least 2 characters."
            )

        return value

    def clean_phone(self):
        phone = self.cleaned_data.get(
            "phone", ""
        ).strip()

        if not phone:
            return ""

        allowed = set("0123456789+- ()")

        if any(char not in allowed for char in phone):
            raise forms.ValidationError(
                "Enter a valid phone number."
            )

        digits = "".join(
            char for char in phone if char.isdigit()
        )

        if not 10 <= len(digits) <= 15:
            raise forms.ValidationError(
                "Phone number must contain 10 to 15 digits."
            )

        return phone
