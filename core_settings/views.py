
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import PharmacyProfileForm
from .models import PharmacyProfile


def can_manage_pharmacy_settings(user):
    """
    Explicit authorization for business configuration.

    Admin role labels alone do not grant access.
    """
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.has_perm(
                "core_settings.change_pharmacyprofile"
            )
        )
    )


@login_required
@require_http_methods(["GET", "POST"])
def pharmacy_settings(request):

    if not can_manage_pharmacy_settings(request.user):
        raise PermissionDenied(
            "You do not have permission to manage "
            "pharmacy settings."
        )

    profile = PharmacyProfile.get_profile()

    if request.method == "POST":

        form = PharmacyProfileForm(
            request.POST,
            request.FILES,
            instance=profile,
        )

        if form.is_valid():

            with transaction.atomic():
                form.save()

            messages.success(
                request,
                "Pharmacy settings updated successfully."
            )

            return redirect(
                "core_settings:pharmacy_settings"
            )

    else:
        form = PharmacyProfileForm(
            instance=profile
        )

    context = {
        "form": form,
        "profile": profile,
    }

    return render(
        request,
        "core_settings/pharmacy_settings.html",
        context,
    )
