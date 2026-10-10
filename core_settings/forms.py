from branches.models import Branch
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
            "enable_multi_branch",
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
            
            "enable_multi_branch": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "role": "switch",
                }
            ),

        }
    
    def __init__(
        self,
        *args,
        allow_branch_toggle=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        # Only the Owner can change deployment mode.
        if not allow_branch_toggle:
            self.fields.pop("enable_multi_branch", None)

    def clean_enable_multi_branch(self):
        enabled = self.cleaned_data["enable_multi_branch"]

        previously_enabled = bool(
            self.instance.pk
            and self.instance.enable_multi_branch
        )

        # Validate only when switching from ON to OFF.
        if previously_enabled and not enabled:
            branch_count = Branch.objects.count()

            if branch_count > 1:
                raise forms.ValidationError(
                    "Multi-Branch Mode cannot be disabled "
                    "while multiple branch records exist. "
                    "Preserve or consolidate branch data "
                    "before switching to Single Pharmacy Mode."
                )

        return enabled

