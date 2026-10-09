"""Shared pharmacy operational settings and inventory alert rules.

The stored stock quantity is always in the medicine's smallest saleable unit.
The pharmacy low-stock level is a system-wide *floor*: a medicine-specific
higher minimum remains respected. No quantities are converted to packs here.
"""
from datetime import timedelta

from django.db.models import F, IntegerField, Value
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone

from .models import PharmacyProfile


DEFAULT_LOW_STOCK = 20
DEFAULT_EXPIRY_DAYS = 30


def get_operational_settings():
    """Read current settings without creating a profile on GET requests."""
    profile = (
        PharmacyProfile.objects
        .filter(pk=1)
        .values("default_tax_percentage", "low_stock_threshold", "expiry_alert_days")
        .first()
    )
    if profile is None:
        return {
            "default_tax_percentage": 0,
            "low_stock_threshold": DEFAULT_LOW_STOCK,
            "expiry_alert_days": DEFAULT_EXPIRY_DAYS,
        }
    return profile


def effective_low_stock_threshold(medicine_threshold, pharmacy_threshold):
    """Return the larger threshold (both expressed in smallest units)."""
    return max(int(medicine_threshold or 0), int(pharmacy_threshold))


def annotate_low_stock_threshold(queryset, pharmacy_threshold):
    """Expose `effective_low_stock_threshold` on each InventoryBatch row."""
    return queryset.annotate(
        effective_low_stock_threshold=Greatest(
            Coalesce(
                F("medicine__minimum_stock_level"),
                Value(0),
                output_field=IntegerField(),
            ),
            Value(int(pharmacy_threshold)),
            output_field=IntegerField(),
        )
    )


def low_stock_batches(queryset, pharmacy_threshold, *, today=None):
    """Active, unexpired, nonempty batches at or below the stock threshold."""
    if today is None:
        today = timezone.localdate()
    return annotate_low_stock_threshold(queryset, pharmacy_threshold).filter(
        is_active=True,
        medicine__is_active=True,
        quantity__gt=0,
        expiry_date__gte=today,
        quantity__lte=F("effective_low_stock_threshold"),
    )


def expiring_soon_batches(queryset, alert_days, *, today=None):
    """Active stocked batches expiring inclusively from today through N days."""
    if today is None:
        today = timezone.localdate()
    until = today + timedelta(days=int(alert_days))
    return queryset.filter(
        is_active=True,
        medicine__is_active=True,
        quantity__gt=0,
        expiry_date__gte=today,
        expiry_date__lte=until,
    )


def scope_inventory_to_user(queryset, user):
    """Superusers see all branches; other users can see only their branch."""
    if getattr(user, "is_superuser", False):
        return queryset
    branch_id = getattr(user, "branch_id", None)
    if branch_id:
        return queryset.filter(branch_id=branch_id)
    return queryset.none()


def expiry_alert_category(expiry_date, alert_days, *, today=None):
    """Pure helper for testing expiry date boundaries."""
    if today is None:
        today = timezone.localdate()
    if expiry_date < today:
        return "expired"
    if expiry_date <= today + timedelta(days=int(alert_days)):
        return "expiring_soon"
    return "valid"
