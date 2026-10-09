
from django import forms

from .models import PharmacyProfile


class PharmacyProfileForm(forms.ModelForm):

    class Meta:
        model = PharmacyProfile

        fields = [
            "name",
            "tagline",
            "logo",
            "phone",
            "email",
            "address",
            "registration_number",
            "currency_code",
            "default_tax_percentage",
            "low_stock_threshold",
            "expiry_alert_days",
            "receipt_footer",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter pharmacy name",
                }
            ),

            "tagline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Business tagline",
                }
            ),

            "logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/png,image/jpeg,image/webp",
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "+92 300 1234567",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "info@pharmacy.com",
                }
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Pharmacy address",
                }
            ),

            "registration_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Business or license number",
                }
            ),

            "currency_code": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "default_tax_percentage": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),

            "low_stock_threshold": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "1",
                }
            ),

            "expiry_alert_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "365",
                    "step": "1",
                }
            ),

            "receipt_footer": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Thank you for visiting!",
                }
            ),
        }
