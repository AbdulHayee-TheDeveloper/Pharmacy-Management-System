
from decimal import Decimal, InvalidOperation

from .models import PharmacyProfile


ZERO = Decimal("0.00")
MAX_TAX = Decimal("100.00")


def get_default_tax_rate():
    """
    Returns the current pharmacy-wide default tax rate.
    Read fresh for each checkout/search request.
    """
    rate = (
        PharmacyProfile.objects
        .filter(pk=1)
        .values_list(
            "default_tax_percentage",
            flat=True,
        )
        .first()
    )

    if rate is None:
        return ZERO

    return Decimal(rate)


def get_effective_tax_rate(
    medicine,
    *,
    default_rate=None,
):
    """
    Resolve the rate from trusted database fields.

    Existing medicines preserve their own tax rates.
    Only explicitly opted-in medicines use the
    pharmacy-wide default.
    """
    if medicine.use_pharmacy_default_tax:
        if default_rate is None:
            default_rate = get_default_tax_rate()

        value = default_rate
    else:
        value = medicine.tax_rate

    try:
        rate = Decimal(str(value if value is not None else 0))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(
            "Invalid medicine tax configuration."
        ) from exc

    if not rate.is_finite() or not (ZERO <= rate <= MAX_TAX):
        raise ValueError(
            "Medicine tax percentage must be between 0 and 100."
        )

    return rate
