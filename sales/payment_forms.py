
from decimal import Decimal

from django import forms

from .models import SalePayment
from .payment_services import get_sale_outstanding


class ReceivePaymentForm(forms.Form):

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "0.01",
            "step": "0.01",
            "placeholder": "Enter amount",
        }),
    )

    payment_method = forms.ChoiceField(
        choices=SalePayment._meta.get_field(
            "payment_method"
        ).choices,
        widget=forms.Select(attrs={
            "class": "form-select",
        }),
    )

    reference_number = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Transaction ID / reference",
        }),
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Optional payment notes",
        }),
    )

    def __init__(self, *args, sale=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.sale = sale

        if sale is not None and not self.is_bound:
            self.fields["amount"].initial = (
                get_sale_outstanding(sale)
            )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]

        if self.sale is not None:
            outstanding = get_sale_outstanding(
                self.sale
            )

            if amount > outstanding:
                raise forms.ValidationError(
                    f"Outstanding balance is "
                    f"Rs. {outstanding:.2f}."
                )

        return amount
