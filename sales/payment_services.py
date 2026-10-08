
from decimal import Decimal, InvalidOperation

from django.db import transaction

from .models import Sale, SalePayment


class PaymentError(Exception):
    pass


MONEY = Decimal("0.01")


def parse_payment_amount(value):
    if isinstance(value, bool):
        raise PaymentError("Invalid payment amount.")

    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise PaymentError("Invalid payment amount.")

    if not amount.is_finite():
        raise PaymentError("Invalid payment amount.")

    if amount <= 0:
        raise PaymentError(
            "Payment amount must be greater than zero."
        )

    if amount != amount.quantize(MONEY):
        raise PaymentError(
            "Payment amount cannot have more than 2 decimal places."
        )

    return amount


def get_sale_outstanding(sale):
    """
    Existing checkout may contain change returned to customer.
    Effective paid = paid_amount - change_amount.
    """

    effective_paid = (
        sale.paid_amount - sale.change_amount
    )

    return max(
        sale.total_amount - effective_paid,
        Decimal("0.00"),
    )


@transaction.atomic
def receive_sale_payment(
    *,
    sale_id,
    user,
    authorized_sales,
    amount,
    payment_method,
    reference_number="",
    notes="",
):
    if (
        user is None
        or not user.is_authenticated
        or not user.is_active
        or not user.has_perm("sales.change_sale")
    ):
        raise PaymentError(
            "You do not have permission to receive payments."
        )

    if authorized_sales is None:
        raise PaymentError(
            "Authorized sales are required."
        )

    allowed_methods = {
        choice[0]
        for choice in SalePayment._meta.get_field(
            "payment_method"
        ).choices
    }

    if payment_method not in allowed_methods:
        raise PaymentError(
            "Invalid payment method."
        )

    amount = parse_payment_amount(amount)

    reference_number = str(
        reference_number or ""
    ).strip()

    if len(reference_number) > 100:
        raise PaymentError(
            "Payment reference is too long."
        )

    notes = str(notes or "").strip()

    try:
        sale = (
            Sale.objects
            .select_for_update()
            .get(
                pk=sale_id,
                pk__in=authorized_sales.values("pk"),
            )
        )
    except Sale.DoesNotExist:
        raise PaymentError(
            "Sale not found or access denied."
        )

    if sale.status != Sale.Status.COMPLETED:
        raise PaymentError(
            "Payments can only be received "
            "against completed sales."
        )

    outstanding = get_sale_outstanding(sale)

    if outstanding <= 0:
        raise PaymentError(
            "This sale is already fully paid."
        )

    if amount > outstanding:
        raise PaymentError(
            f"Maximum outstanding payment is Rs. {outstanding:.2f}."
        )

    payment = SalePayment.objects.create(
        sale=sale,
        amount=amount,
        payment_method=payment_method,
        reference_number=reference_number,
        notes=notes,
        received_by=user,
    )

    sale.paid_amount += amount

    remaining = get_sale_outstanding(sale)

    if remaining == 0:
        sale.payment_status = Sale.PaymentStatus.PAID

    elif sale.paid_amount - sale.change_amount > 0:
        sale.payment_status = Sale.PaymentStatus.PARTIAL

    else:
        sale.payment_status = Sale.PaymentStatus.UNPAID

    sale.save(
        update_fields=[
            "paid_amount",
            "payment_status",
            "updated_at",
        ]
    )

    return payment
