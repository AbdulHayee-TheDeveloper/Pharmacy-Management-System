
"""Branch resolution for Single Pharmacy Mode."""

from django.core.exceptions import ValidationError
from django.db import transaction

from core_settings.models import PharmacyProfile
from .models import Branch


def ensure_single_pharmacy_branch():
    """
    Resolve the default pharmacy branch.

    Single Pharmacy Mode:
        1. No branch -> Create default MAIN branch.
        2. One active branch -> Use existing branch.
        3. Multiple branches -> Raise validation error.
        4. Inactive branch -> Raise validation error.

    Multi-Branch Mode:
        Branch selection is handled separately.
    """

    profile = PharmacyProfile.get_profile()

    if profile.enable_multi_branch:
        raise ValidationError(
            "Single Pharmacy Mode is not enabled."
        )

    with transaction.atomic():

        branches = list(
            Branch.objects
            .select_for_update()
            .order_by("pk")[:2]
        )

        # Multiple existing branches must not be
        # automatically merged or selected.
        if len(branches) > 1:
            raise ValidationError(
                "Multiple branches already exist. "
                "Enable Multi-Branch Mode in Pharmacy Settings."
            )

        # Reuse the existing branch.
        if branches:
            branch = branches[0]

            if not branch.is_active:
                raise ValidationError(
                    "The only pharmacy branch is inactive. "
                    "Activate it before adding inventory."
                )

            return branch

        # Fresh installation: create one default branch.
        branch, _ = Branch.objects.get_or_create(
            code="MAIN",
            defaults={
                "name": (
                    profile.name or "Main Pharmacy"
                )[:100],
                "is_active": True,
            },
        )

        return branch
